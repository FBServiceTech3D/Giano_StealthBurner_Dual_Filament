import time
from ssl import SSLSocket
from math import fabs
from re import T
import logging

class ROME:

    # -----------------------------------------------------------------------------------------------------------------------------
    # Initialize
    # -----------------------------------------------------------------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.printer = self.config.get_printer()
        self.reactor = self.printer.get_reactor()
        self.gcode = self.printer.lookup_object('gcode')
        self.toolhead_filament_sensor = self.printer.lookup_object("filament_switch_sensor toolhead_filament_sensor")
        self.f1_filament_sensor = None
        self.f2_filament_sensor = None
        self.y1_filament_sensor = None
        self.y2_filament_sensor = None
        self.z_filament_sensor = None

        self.load_settings()
        self.register_commands()
        self.register_handle_connect()

    def load_settings(self):
        self.idler_stepper = None

        self.rome_setup = self.config.getint('rome_setup', 0)

        self.Filament_Cache = []
        self.tool_count = self.config.getint('tool_count', 2)
        for i in range(1, self.tool_count + 1):
            self.Filament_Cache.append(False)

        self.idle_timeout = self.config.getint('idle_timeout', 3600)
        self.heater_timeout = self.config.getfloat('heater_timeout', 600.0)
        self.unload_filament_after_print = self.config.getfloat('unload_filament_after_print', 1)
        self.wipe_tower_acceleration = self.config.getfloat('wipe_tower_acceleration', 5000.0)
        self.use_ooze_ex = self.config.getfloat('use_ooze_ex', 1)

        self.runout_detected = False
        self.infinite_spool = False

        if self.config.getfloat('use_filament_caching', 1) == 1:
            self.use_filament_caching = True
        else:
            self.use_filament_caching = False
        #self.Filament_Groups = self.config.getlists('filament_groups', None)

        if self.config.getfloat('extruder_push_and_pull_test', 1) == 1:
            self.extruder_push_and_pull_test = True
        else:
            self.extruder_push_and_pull_test = False

        self.nozzle_loading_speed_mms = self.config.getfloat('nozzle_loading_speed_mms', 10.0)
        self.filament_homing_speed_mms = self.config.getfloat('filament_homing_speed_mms', 75.0)
        self.filament_parking_speed_mms = self.config.getfloat('filament_parking_speed_mms', 50.0)

        self.toolhead_sensor_to_bowden_cache_mm = self.config.getfloat('toolhead_sensor_to_bowden_cache_mm', 100.0)
        self.toolhead_sensor_to_bowden_parking_mm = self.config.getfloat('toolhead_sensor_to_bowden_parking_mm', 100.0)
        self.toolhead_sensor_to_extruder_gear_mm = self.config.getfloat('toolhead_sensor_to_extruder_gear_mm', 45.0)
        self.extruder_gear_to_parking_position_mm = self.config.getfloat('extruder_gear_to_parking_position_mm', 40.0)
        self.parking_position_to_nozzle_mm = self.config.getfloat('parking_position_to_nozzle_mm', 65.0)

    def register_handle_connect(self):
        self.printer.register_event_handler("klippy:connect", self.execute_handle_connect)

    def execute_handle_connect(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        self.extruder = self.printer.lookup_object('extruder')
        self.pheaters = self.printer.lookup_object('heaters')
        self.heater = self.extruder.get_heater()

        if self.rome_setup == 1:
            for manual_stepper in self.printer.lookup_objects('manual_stepper'):
                rail_name = manual_stepper[1].get_steppers()[0].get_name()
                if rail_name == 'manual_stepper idler_stepper':
                    self.idler_stepper = manual_stepper[1]
            if self.idler_stepper is None:
                raise self.config.error("Idler Stepper not found!")

        for filament_sensor in self.printer.lookup_objects('filament_switch_sensor'):
            sensor_name = filament_sensor[1].runout_helper.name
            if sensor_name == 'feeder_1_filament_sensor':
                self.f1_filament_sensor = filament_sensor[1]
            if sensor_name == 'feeder_2_filament_sensor':
                self.f2_filament_sensor = filament_sensor[1]
            if sensor_name == 'y1_filament_sensor':
                self.y1_filament_sensor = filament_sensor[1]
            if sensor_name == 'y2_filament_sensor':
                self.y2_filament_sensor = filament_sensor[1]
            if sensor_name == 'z_filament_sensor':
                self.z_filament_sensor = filament_sensor[1]

    # -----------------------------------------------------------------------------------------------------------------------------
    # Heater Timeout Handler
    # -----------------------------------------------------------------------------------------------------------------------------
    def enable_heater_timeout(self):
        waketime = self.reactor.NEVER
        if self.heater_timeout:
            waketime = self.reactor.monotonic() + self.heater_timeout
        self.heater_timeout_handler = self.reactor.register_timer(self.execute_heater_timeout, waketime)

    def disable_heater_timeout(self):
        if self.heater_timeout_handler:
            self.reactor.update_timer(self.heater_timeout_handler, self.reactor.NEVER)

    def execute_heater_timeout(self, eventtime):
        if self.Paused:
            self.respond("Heater timeout detected!")
            self.extruder_set_temperature(0, False)
        nextwake = self.reactor.NEVER
        return nextwake

    # -----------------------------------------------------------------------------------------------------------------------------
    # G-Code Registration
    # -----------------------------------------------------------------------------------------------------------------------------
    def register_commands(self):
        self.gcode.register_command('HOME_ROME', self.cmd_HOME_ROME, desc=("HOME_ROME"))
        self.gcode.register_command('LOAD_TOOL', self.cmd_LOAD_TOOL, desc=("LOAD_TOOL"))
        self.gcode.register_command('SELECT_TOOL', self.cmd_SELECT_TOOL, desc=("SELECT_TOOL"))
        self.gcode.register_command('UNLOAD_TOOL', self.cmd_UNLOAD_TOOL, desc=("UNLOAD_TOOL"))
        self.gcode.register_command('EJECT_TOOL', self.cmd_EJECT_TOOL, desc=("EJECT_TOOL"))
        self.gcode.register_command('CHANGE_TOOL', self.cmd_CHANGE_TOOL, desc=("CHANGE_TOOL"))
        self.gcode.register_command('ROME_END_PRINT', self.cmd_ROME_END_PRINT, desc=("ROME_END_PRINT"))
        self.gcode.register_command('ROME_START_PRINT', self.cmd_ROME_START_PRINT, desc=("ROME_START_PRINT"))
        self.gcode.register_command('ROME_INSERT_GCODE', self.cmd_ROME_INSERT_GCODE, desc=("ROME_INSERT_GCODE"))
        self.gcode.register_command('ROME_RUNOUT_GCODE', self.cmd_ROME_RUNOUT_GCODE, desc=("ROME_RUNOUT_GCODE"))
        self.gcode.register_command('LOAD_FILAMENTS', self.cmd_LOAD_FILAMENTS, desc=("LOAD_FILAMENTS"))
        self.gcode.register_command('Z_HOME_TEST', self.cmd_Z_HOME_TEST, desc=("Z_HOME_TEST"))
        self.gcode.register_command('F_RUNOUT', self.cmd_F_RUNOUT, desc=("F_RUNOUT"))
        self.gcode.register_command('F_INSERT', self.cmd_F_INSERT, desc=("F_INSERT"))
        self.gcode.register_command('_SET_INFINITE_SPOOL', self.cmd_SET_INFINITE_SPOOL, desc=("SET_INFINITE_SPOOL"))

    def cmd_SELECT_TOOL(self, param):
        tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
        self.select_tool(tool)

    def cmd_LOAD_TOOL(self, param):
        self.cmd_origin = "gcode"
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)
        
        # load tool
        if not self.load_tool(tool, temp, True):

            # send notification
            self.gcode.run_script_from_command('_EXTRUDER_ERROR EXTRUDER=' + str(tool))

            self.pause_rome()
            return
        
        return
    
    def cmd_UNLOAD_TOOL(self, param):
        self.cmd_origin = "gcode"
        tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
        temp = param.get_int('TEMP', None, minval=-1, maxval=self.heater.max_temp)

        # set hotend temperature
        if temp > 0:
            self.set_hotend_temperature(temp)

        # unload tool
        self.Selected_Filament = tool
        if self.toolhead_filament_sensor_triggered():
            self.unload_tool(-1, False)

    def cmd_EJECT_TOOL(self, param):
        tool = param.get_int('TOOL', None, minval=-1, maxval=self.tool_count)
        self.eject_filament(tool)

    def cmd_HOME_ROME(self, param):
        self.Homed = False
        if not self.home():
            self.respond("Can not home ROME!")

    def cmd_CHANGE_TOOL(self, param):
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        if not self.change_tool(tool):
            self.pause_rome()

    def cmd_ROME_END_PRINT(self, param):
        self.cmd_origin = "gcode"
        self.infinite_spool = False
        self.gcode.run_script_from_command("END_PRINT")
        if self.unload_filament_after_print == 1:
            if self.toolhead_filament_sensor_triggered():
                self.unload_tool(-1, False)
            if self.use_filament_caching:
                self.uncache_all()
            self.gcode.run_script_from_command('M84')
        self.Homed = False

    def cmd_ROME_START_PRINT(self, param):
        self.cmd_origin = "rome"
        self.mode = "native"
        self.infinite_spool = False
        self.Filament_Changes = 0
        self.exchange_old_position = None

        self.Filament_Cache = []
        for i in range(1, self.tool_count + 1):
            self.Filament_Cache.append(False)

        self.wipe_tower_x = param.get_float('WIPE_TOWER_X', None, minval=0, maxval=999) 
        self.wipe_tower_y = param.get_float('WIPE_TOWER_Y', None, minval=0, maxval=999)
        self.wipe_tower_width = param.get_float('WIPE_TOWER_WIDTH', None, minval=0, maxval=999)
        self.wipe_tower_rotation_angle = param.get_float('WIPE_TOWER_ROTATION_ANGLE', None, minval=-360, maxval=360)

        cooling_tube_retraction = param.get_float('COOLING_TUBE_RETRACTION', None, minval=0, maxval=999) 
        cooling_tube_length = param.get_float('COOLING_TUBE_LENGTH', None, minval=0, maxval=999) 
        parking_pos_retraction = param.get_float('PARKING_POS_RETRACTION', None, minval=0, maxval=999) 
        extra_loading_move = param.get_float('EXTRA_LOADING_MOVE', None, minval=-999, maxval=999) 
        if cooling_tube_retraction == 0 and cooling_tube_length == 0 and parking_pos_retraction == 0 and extra_loading_move == 0:
            self.mode = "native"
        else:
            self.mode = "slicer"
        
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        bed_temp = param.get_int('BED_TEMP', None, minval=-1, maxval=self.heater.max_temp)
        extruder_temp = param.get_int('EXTRUDER_TEMP', None, minval=-1, maxval=self.heater.max_temp)
        chamber_temp = param.get_int('CHAMBER_TEMP', None, minval=0, maxval=70)

        self.disable_toolhead_filament_sensor()

        self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=RatOS VARIABLE=relative_extrusion VALUE=True")
        self.gcode.run_script_from_command("SET_GCODE_VARIABLE MACRO=_START_PRINT_AFTER_HEATING_EXTRUDER VARIABLE=tool VALUE=" + str(tool + 1))
        self.gcode.run_script_from_command("START_PRINT BED_TEMP=" + str(bed_temp) + " EXTRUDER_TEMP=" + str(extruder_temp) + " CHAMBER_TEMP=" + str(chamber_temp))

    def cmd_ROME_INSERT_GCODE(self, param):
        self.insert_gcode()

    def cmd_ROME_RUNOUT_GCODE(self, param):
        self.runout_gcode()

    def cmd_LOAD_FILAMENTS(self, param):
        if not self.Homed:
            if not self.home():
                return False
        if not self.home_filaments():
            return False
        return True

    def cmd_Z_HOME_TEST(self, param):
        if not self.Homed:
            if not self.home():
                return False
        if not self.home_filaments():
            return False
        return True

    def cmd_F_INSERT(self, param):
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        if self.filament_insert(tool):
            self.gcode.run_script_from_command('_AUTOLOAD_RESUME_AFTER_INSERT TOOL=' + str(tool))

    def cmd_F_RUNOUT(self, param):
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        if self.filament_runout(tool):
            self.gcode.run_script_from_command('_INFINITE_RESUME_AFTER_SWAP TOOL=' + str(tool))

    def cmd_SET_INFINITE_SPOOL(self, param):
        self.infinite_spool = not self.infinite_spool
        self.respond("Infinite Spool: " + str(self.infinite_spool))

    # -----------------------------------------------------------------------------------------------------------------------------
    # Home
    # -----------------------------------------------------------------------------------------------------------------------------
    Homed = False

    def home(self):

        # homing rome
        self.respond("Homing Rome!")
        self.Homed = False
        self.Paused = False

        # precheck
        if not self.can_home():
            return False

        # home rome types
        if self.rome_setup == 0:
            # home extruder feeder
            if not self.home_extruder_feeder():
                return False
        elif self.rome_setup == 1:
            # home mmu splitter
            if not self.home_mmu_splitter():
                return False

        # success
        self.Homed = True
        self.Selected_Filament = -1
        self.respond("Welcome Home Rome!")
        return True

    def can_home(self):
        
        # check hotend temperature
        if not self.extruder_can_extrude():
            self.respond("Preheat Nozzle to " + str(self.heater.min_extrude_temp + 10))
            self.extruder_set_temperature(self.heater.min_extrude_temp + 10, True)

        # check extruder
        if self.toolhead_filament_sensor_triggered():

            # unload filament from nozzle
            if self.toolhead_filament_sensor_triggered():
                if not self.unload_tool(-1, False):
                    self.respond("Can not unload from nozzle!")
                    return False

            # turn off hotend heater
            self.extruder_set_temperature(0, False)

            # check
            if self.toolhead_filament_sensor_triggered():
                self.respond("Filament stuck in extruder!")
                return False

        # success
        return True

    def home_filaments(self):
     
        # home filaments
        if self.rome_setup == 0:
            if not self.home_extruder_filaments():
                return False
        elif self.rome_setup == 1:
            if not self.home_mmu_splitter_filaments():
                return False

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Home Extruder Feeder
    # -----------------------------------------------------------------------------------------------------------------------------

    def home_extruder_feeder(self):
    
        # success
        return True

    def home_extruder_filaments(self):
         
        # home all filaments
        for i in range(1, self.tool_count + 1):
            if not self.home_extruder_filament(i):
                return False

        # success
        return True

    def home_extruder_filament(self, filament):
         
        # select tool
        self.select_tool(filament)

        # home filament
        if not self.load_filament_from_reverse_bowden_to_toolhead_sensor(False):
            self.respond("Filament " + str(filament) + " cant be loaded into the toolhead sensor!")
            return False
        if not self.unload_filament_from_toolhead_sensor(-1, -1):
            self.respond("Filament " + str(filament) + " cant be unloaded from the toolhead sensor!")
            return False

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Home MMU Splitter
    # -----------------------------------------------------------------------------------------------------------------------------
    idler_selecting_speed = 125
    idler_selecting_accel = 80
    idler_home_position = 85
    idler_homeing_speed = 40
    idler_homeing_accel = 40
    idler_positions = [5,20,35,50,65]

    def home_mmu_splitter(self):
        
        # home idler
        self.home_idler()

        # success
        return True

    def home_idler(self):
        home_current = 0.1
        driver_status = self.stepper_driver_status('idler_stepper')
        self.gcode.run_script_from_command('SET_TMC_CURRENT STEPPER=idler_stepper CURRENT=' + str(home_current) + ' HOLDCURRENT=' + str(home_current))
        self.idler_stepper.do_set_position(0.0)
        self.stepper_move(self.idler_stepper, 7, True, self.idler_homeing_speed, self.idler_homeing_accel)
        self.stepper_homing_move(self.idler_stepper, -95, True, self.idler_homeing_speed, self.idler_homeing_accel, 1)
        self.idler_stepper.do_set_position(2.0)
        self.stepper_move(self.idler_stepper, self.idler_home_position, True, self.idler_homeing_speed, self.idler_homeing_accel)
        self.gcode.run_script_from_command('SET_TMC_CURRENT STEPPER=idler_stepper CURRENT=' + str(driver_status['run_current']) + ' HOLDCURRENT=' + str(driver_status['hold_current']))

    def home_mmu_splitter_filaments(self):
         
        # home all filaments
        for i in range(1, self.tool_count + 1):
            if not self.home_mmu_splitter_filament(i):
                self.respond("could not home filaments!")
                return False

        # success
        return True

    def home_mmu_splitter_filament(self, filament):
         
        # select tool
        self.select_tool(filament)

        # home filament
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E100 F' + str(self.filament_homing_speed_mms * 60))
        self.gcode.run_script_from_command('M400')
        if not self.y_filament_sensor_triggered():
            self.respond("filament " + str(filament) + " not found!")
            return True

        # park filament
        if not self.park_filament():
            self.respond("could not park filament " + str(filament) + "!")
            return False

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Autoload
    # -----------------------------------------------------------------------------------------------------------------------------

    def filament_insert(self, tool):
        logging.info("auto loading filament " + str(tool))
        self.respond("auto loading filament " + str(tool))

        if self.rome_setup == 0:

            # check hotend temperature
            if not self.extruder_can_extrude():
                self.respond("Hotend too cold!")
                self.respond("Heating up nozzle to " + str(self.heater.min_extrude_temp))
                self.extruder_set_temperature(self.heater.min_extrude_temp, True)

            # select filament
            self.select_tool(tool)

            # move filament to the caching position
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E50 F1000')
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E' + str(self.toolhead_sensor_to_bowden_parking_mm - 50) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')

            # load filament to nozzle
            if self.runout_detected == True:
                self.runout_detected = False
                self.cmd_origin = "gcode"

                # load tool
                if not self.load_tool(tool, -1, True):
                    # send notification
                    self.gcode.run_script_from_command('_EXTRUDER_ERROR EXTRUDER=' + str(tool))
                    self.respond("Autoload failed, please insert filament " + str(tool) + " and resume the print.")
                    return False

                return True
        return False

    def eject_filament(self, tool):
        logging.info("eject filament " + str(tool))
        self.respond("eject filament " + str(tool))

        # check hotend temperature
        if not self.extruder_can_extrude():
            self.respond("Hotend too cold!")
            self.respond("Heating up nozzle to " + str(self.heater.min_extrude_temp))
            self.extruder_set_temperature(self.heater.min_extrude_temp, True)

        if self.rome_setup == 0:
            # select filament
            self.select_tool(tool)

            # eject filament
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_bowden_parking_mm + 100) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')

            # success
            return True

        return False

    def filament_runout(self, tool):
        logging.info("runout detected filament " + str(tool))
        self.respond("runout detected filament " + str(tool))

        # unload tool
        if self.Selected_Filament == tool:
            self.runout_detected = True

            if not self.unload_tool(-1, False):
                self.respond("could not unload tool!")
                return False

            self.eject_filament(tool)
        
        if self.infinite_spool == True:

            if tool == 1:
                tool = 2
            elif tool == 2:
                tool = 1
        
            self.select_tool(tool)

            # load tool
            if not self.load_tool(tool, -1, True):
                # send notification
                self.gcode.run_script_from_command('_EXTRUDER_ERROR EXTRUDER=' + str(tool))
                self.respond("Autload failed, please insert filament " + str(tool) + " and resume the print.")
                return False

            return True
        return False

    # -----------------------------------------------------------------------------------------------------------------------------
    # Change Tool
    # -----------------------------------------------------------------------------------------------------------------------------
    mode = "native"
    cmd_origin = "rome"

    Filament_Changes = 0
    ooze_move_x = 0
    exchange_old_position = None

    wipe_tower_x = 170
    wipe_tower_y = 140
    wipe_tower_width = 60
    wipe_tower_rotation_angle = 0

    def change_tool(self, tool):
        self.respond("change_tool " + str(tool + 1))

        self.cmd_origin = "rome"

        # change tool
        if self.Filament_Changes > 0:
            self.before_change()
            if not self.load_tool(tool + 1, -1, self.use_filament_caching):

                # send notification
                self.gcode.run_script_from_command('_EXTRUDER_ERROR EXTRUDER=' + str(tool))

                return False
            self.after_change()
        self.Filament_Changes = self.Filament_Changes + 1

        # success
        return True

    def load_tool(self, tool, temp, cache):
        logging.info("load_tool " + str(tool))
        self.respond("load_tool " + str(tool))
        
        # send notification
        self.gcode.run_script_from_command('_SELECT_EXTRUDER EXTRUDER=' + str(tool))

        # set hotend temperature
        if temp > 0:
            self.set_hotend_temperature(temp)

        # home if not homed yet
        if not self.Homed:
            if not self.home():
                return False

        # set temp if configured and wait for it
        if temp > 0:
            self.respond("Waiting for heater...")
            self.extruder_set_temperature(temp, True)

        # check hotend temperature
        if not self.extruder_can_extrude():
            self.respond("Hotend too cold!")
            self.respond("Heat up nozzle to " + str(self.heater.min_extrude_temp))
            self.extruder_set_temperature(self.heater.min_extrude_temp, True)

        # enable filament sensor
        self.enable_toolhead_filament_sensor()

        # load filament
        if self.toolhead_filament_sensor_triggered():
            if not self.unload_tool(tool, cache):
                self.respond("could not unload tool!")
                return False
        else:
            if self.cmd_origin == "rome":
                self.respond("Possible sensor failure!")
                self.respond("Filament sensor should be triggered but it isnt!")
                return False

        self.select_tool(tool)
        if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
            self.respond("could not load tool to sensor!")
            return False
        if not self.load_filament_from_toolhead_sensor_to_parking_position():
            return False
        if self.mode != "slicer" or self.Filament_Changes == 0:
            if not self.load_filament_from_parking_position_to_nozzle():
                self.respond("could not load into nozzle!")
                return False

        # success
        self.respond("tool " + str(tool) + " loaded")

        # send notification
        self.gcode.run_script_from_command('_EXTRUDER_SELECTED EXTRUDER=' + str(tool))

        return True

    def unload_tool(self, new_filament, cache):

        # select tool
        self.select_tool(self.Selected_Filament)

        # unload tool
        if self.mode != "slicer":
            if not self.unload_filament_from_nozzle_to_parking_position():
                return False
        if not self.unload_filament_from_parking_position_to_toolhead_sensor():
            return False
        if not self.unload_filament_from_toolhead_sensor(new_filament, cache):
            return False

        # test if filament has been unloaded behind the y-sensor
        if not cache:
            if self.y_filament_sensor_triggered():
                self.respond("Unload not completed!")
                return False

        # release mmu splitter idler
        if self.rome_setup == 1:
            self.select_idler(-1)

        # success
        return True

    def before_change(self):
        if self.mode == "native":
            self.before_change_rome_native()
        elif self.mode == "slicer":
            self.before_change_rome_slicer()
        
    def after_change(self):
        self.disable_toolhead_filament_sensor()

        # send notification
        self.gcode.run_script_from_command('_CONTINUE_PRINTING EXTRUDER=' + str(self.Selected_Filament))

    # -----------------------------------------------------------------------------------------------------------------------------
    # Rome Native
    # -----------------------------------------------------------------------------------------------------------------------------

    def before_change_rome_native(self):
        self.gcode.run_script_from_command('SAVE_GCODE_STATE NAME=PAUSE_state')
        self.exchange_old_position = self.toolhead.get_position()

        x_offset = abs(self.exchange_old_position[0] - self.wipe_tower_x)
        if x_offset < 10:
            self.ooze_move_x = self.wipe_tower_x + self.wipe_tower_width
        else:
            self.ooze_move_x = self.exchange_old_position[0] - self.wipe_tower_width

        self.gcode.run_script_from_command('M204 S' + str(self.wipe_tower_acceleration))
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E-2 F3600')
        self.gcode.run_script_from_command('M400')
        
    # -----------------------------------------------------------------------------------------------------------------------------
    # Rome Slicer
    # -----------------------------------------------------------------------------------------------------------------------------

    def before_change_rome_slicer(self):
        self.respond("before_change_rome_slicer")
        self.gcode.run_script_from_command('SAVE_GCODE_STATE NAME=PAUSE_state')
        self.exchange_old_position = self.toolhead.get_position()
        self.gcode.run_script_from_command('M204 S' + str(self.wipe_tower_acceleration))
        
    # -----------------------------------------------------------------------------------------------------------------------------
    # Select Tool
    # -----------------------------------------------------------------------------------------------------------------------------
    Selected_Filament = -1

    def select_tool(self, tool=-1):
        if tool == 0:
            self.respond("unselecting tools")
        elif tool == -1:
            self.respond("selecting all tools")
        else:
            self.respond("selecting tool " + str(tool))
        self.unselect_tool()
        if self.rome_setup == 0:
            self.select_tool_extruder_feeder(tool)
        elif self.rome_setup == 1:
            self.select_tool_mmu_splitter(tool)
        self.Selected_Filament = tool
        self.respond("tool " + str(tool) + " selected")

    def select_tool_extruder_feeder(self, tool):
        if tool != 0:
            for i in range(1, self.tool_count + 1):
                if tool == i or tool == -1:
                    self.gcode.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=rome_extruder_' + str(i) + ' MOTION_QUEUE=extruder')

    def select_tool_mmu_splitter(self, tool):
        self.select_idler(tool)

    def unselect_tool(self):
        if self.rome_setup == 0:
            self.unselect_tool_extruder_feeder()
        elif self.rome_setup == 1:
            self.unselect_tool_mmu_splitter()

    def unselect_tool_extruder_feeder(self):
        self.Selected_Filament = -1
        for i in range(1, self.tool_count + 1):
            self.gcode.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=rome_extruder_' + str(i) + ' MOTION_QUEUE=')

    def unselect_tool_mmu_splitter(self):
        self.select_idler(-1)

    def select_idler(self, tool):
        if tool >= 0:
            self.stepper_move(self.idler_stepper, self.idler_positions[tool - 1], True, self.idler_selecting_speed, self.idler_selecting_accel)
            self.gcode.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=pulley_extruder MOTION_QUEUE=extruder')
        else:
            self.stepper_move(self.idler_stepper, self.idler_home_position, True, self.idler_selecting_speed, self.idler_selecting_accel)
            self.gcode.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=pulley_extruder MOTION_QUEUE=')

    # -----------------------------------------------------------------------------------------------------------------------------
    # Load Filament
    # -----------------------------------------------------------------------------------------------------------------------------
    def load_filament_from_reverse_bowden_to_toolhead_sensor(self, exact_positioning=True):
        self.respond("load_filament_from_reverse_bowden_to_toolhead_sensor")

        # set load distance
        load_distance = self.toolhead_sensor_to_bowden_parking_mm
        if self.rome_setup == 0:
            load_distance = self.toolhead_sensor_to_bowden_cache_mm

        # filament caching
        is_cached = False
        if self.use_filament_caching == True:
            if self.tool_count > 2:
                if self.is_filament_cached(self.Selected_Filament):
                    is_cached = False
                    self.respond("Filament " + str(self.Selected_Filament) + " is cached!")
                    load_distance = self.toolhead_sensor_to_bowden_cache_mm
                else:
                    demanded_filament = self.Selected_Filament
                    blocked_filament = self.is_cache_blocked(demanded_filament)
                    if blocked_filament >= 0:
                        self.respond("Filament " + str(demanded_filament) + " is blocked by filament " + str(blocked_filament))
                        if not self.unload_filament_from_caching_position_to_reverse_bowden(blocked_filament):
                            self.pause_rome()
                        else:
                            self.select_tool(demanded_filament)

        # find filament
        if self.rome_setup == 1:
            find_distance = 100
            if is_cached:
                load_distance = load_distance - find_distance
                self.gcode.run_script_from_command('G92 E0')
                self.gcode.run_script_from_command('G0 E' + str(find_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
                self.gcode.run_script_from_command('M400')
                if not self.y_filament_sensor_triggered():
                    self.gcode.run_script_from_command('G92 E0')
                    self.gcode.run_script_from_command('G0 E-' + str(find_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
                    self.gcode.run_script_from_command('M400')
                    self.respond("Could not find filament " + str(self.Selected_Filament) + "!")
                    return False
        self.respond("Filament " + str(self.Selected_Filament) + " found!")
        
        # initial move
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E' + str(load_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # try to find the sensor
        self.respond("try to find the sensor...")
        step_distance = 20
        max_step_count = 50
        if not self.toolhead_filament_sensor_triggered():
            for i in range(max_step_count):
                self.gcode.run_script_from_command('G92 E0')
                self.gcode.run_script_from_command('G0 E' + str(step_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
                self.gcode.run_script_from_command('M400')
                if self.toolhead_filament_sensor_triggered():
                    break

        # check if sensor was found
        self.respond("check if sensor was found...")
        if not self.toolhead_filament_sensor_triggered():
            self.respond("Could not find filament sensor!")
            return False

        # exact positioning
        if exact_positioning == True:
            if not self.filament_positioning():
                self.respond("Could not position the filament in the filament sensor!")
                return False

        # success
        return True

    def load_filament_from_toolhead_sensor_to_parking_position(self):
        self.respond("load_filament_from_toolhead_sensor_to_parking_position")

        # move filament to parking position
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm) + ' F' + str(self.filament_parking_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # extruder push and pull test
        if self.extruder_push_and_pull_test:
            push_and_pull_offset = 10
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset) + ' F' + str(self.filament_parking_speed_mms * 60))
            self.gcode.run_script_from_command('M400')
            if not self.toolhead_filament_sensor_triggered():
                self.respond("could not load filament into extruder!")
                return False
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset) + ' F' + str(self.filament_parking_speed_mms * 60))
            self.gcode.run_script_from_command('M400')

        # success
        return True

    def load_filament_from_parking_position_to_nozzle(self):
        self.respond("load_filament_from_parking_position_to_nozzle")

        # load filament into nozzle
        self.gcode.run_script_from_command('G92 E0')
        if self.cmd_origin != "rome" or self.exchange_old_position == None or self.use_ooze_ex == 0:
            self.gcode.run_script_from_command('G0 E' + str(self.parking_position_to_nozzle_mm) + ' F' + str(self.nozzle_loading_speed_mms * 60))
        else:
            self.gcode.run_script_from_command('G0 E' + str(self.parking_position_to_nozzle_mm / 2) + ' X' + str(self.ooze_move_x) + ' F' + str(self.nozzle_loading_speed_mms * 60))
            self.gcode.run_script_from_command('G0 E' + str(self.parking_position_to_nozzle_mm / 2) + ' X' + str(self.exchange_old_position[0]) + ' F' + str(self.nozzle_loading_speed_mms * 60))
        self.gcode.run_script_from_command('G4 P1000')
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('M400')

        # release mmu splitter idler
        if self.rome_setup == 1:
            self.select_idler(-1)

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Unload Filament
    # -----------------------------------------------------------------------------------------------------------------------------

    def unload_filament_from_nozzle_to_parking_position(self):
        self.respond("unload_filament_from_nozzle_to_parking_position")

        # unload filament to parking position
        if self.cmd_origin != "rome" or self.exchange_old_position == None or self.use_ooze_ex == 0:
            self.gcode.run_script_from_command('_UNLOAD_FROM_NOZZLE_TO_PARKING_POSITION PAUSE=3000')
        else:
            self.gcode.run_script_from_command('_UNLOAD_FROM_NOZZLE_TO_PARKING_POSITION PAUSE=1')
            self.gcode.run_script_from_command('G0 X' + str(self.ooze_move_x) + ' F600')

        # success
        return True

    def unload_filament_from_parking_position_to_toolhead_sensor(self):
        self.respond("unload_filament_from_parking_position_to_toolhead_sensor")
        
        # select mmu splitter idler
        if self.rome_setup == 1:
            self.select_idler(self.Selected_Filament)

        # unload filament to toolhead sensor
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('M400')
        if self.cmd_origin != "rome" or self.exchange_old_position == None or self.use_ooze_ex == 0:
            self.gcode.run_script_from_command('G0 E-' + str(self.extruder_gear_to_parking_position_mm + self.toolhead_sensor_to_extruder_gear_mm) + ' F' + str(self.filament_parking_speed_mms * 60))
        else:
            self.gcode.run_script_from_command('G0 E-' + str(self.extruder_gear_to_parking_position_mm + self.toolhead_sensor_to_extruder_gear_mm) + ' X' + str(self.exchange_old_position[0]) + ' F' + str(self.filament_parking_speed_mms * 60))
            # self.gcode.run_script_from_command('G0 E-' + str(self.extruder_gear_to_parking_position_mm) + ' X' + str(self.exchange_old_position[0]) + ' F' + str(self.filament_parking_speed_mms * 60))
            # self.gcode.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_extruder_gear_mm) + ' F' + str(self.filament_parking_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # success
        return True

    def unload_filament_from_toolhead_sensor(self, new_filament, cache):
        self.respond("unload_filament_from_toolhead_sensor")
        self.respond("new_filament " + str(new_filament))

        # set unload distance
        unload_distance = self.toolhead_sensor_to_bowden_parking_mm
        if self.rome_setup == 0:
            unload_distance = self.toolhead_sensor_to_bowden_cache_mm

        # filament caching
        is_cached = False
        if cache == True and self.tool_count > 2 and new_filament >= 0:
            if not self.is_in_same_filament_group(new_filament, self.Selected_Filament):
                self.respond("filament is not in same filament group, caching filament " + str(self.Selected_Filament))
                self.cache_filament(self.Selected_Filament)
                unload_distance = self.toolhead_sensor_to_bowden_cache_mm
                is_cached = True

        # eject filament
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E-' + str(unload_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # check if filament is ejected from toolhead
        if self.toolhead_filament_sensor_triggered():
            return False

        # park filament
        if self.rome_setup == 1:
            if not is_cached:
                if not self.park_filament():
                    return False

        # uncache filament
        if not is_cached:
            self.uncache_filament(self.Selected_Filament)

        # success
        return True

    def unload_filament_from_caching_position_to_reverse_bowden(self, filament):
        self.respond("unload_filament_from_caching_position_to_reverse_bowden")
        
        # select filament
        self.select_tool(filament)

        # eject filament
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_bowden_parking_mm - self.toolhead_sensor_to_bowden_cache_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # check if filament is ejected
        if self.toolhead_filament_sensor_triggered():
            return False

        # park filament
        if self.rome_setup == 1:
            if not self.park_filament():
                return False

        # uncache filament
        self.uncache_filament(self.Selected_Filament)

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Parking Parking
    # -----------------------------------------------------------------------------------------------------------------------------
    def park_filament(self):
    
        # try to find the y sensor
        self.respond("try to find the sensor...")
        step_distance = 20
        max_step_count = 50
        if self.y_filament_sensor_triggered():
            for i in range(max_step_count):
                self.gcode.run_script_from_command('G92 E0')
                self.gcode.run_script_from_command('G0 E-' + str(step_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
                self.gcode.run_script_from_command('M400')
                if not self.y_filament_sensor_triggered():
                    break

        # check if y sensor was found
        self.respond("check if y sensor was found...")
        if self.y_filament_sensor_triggered():
            self.respond("Y sensor should not be triggered!")
            return False

        # parking
        if not self.filament_parking():
            self.respond("Could not park the filament in the parking sensor!")
            return False

        # parking filament in final parking position
        self.gcode.run_script_from_command('G92 E0')
        self.gcode.run_script_from_command('G0 E-48 F' + str(self.filament_homing_speed_mms * 60))
        self.gcode.run_script_from_command('M400')

        # success
        return True

    def filament_parking(self):

        # fast parking
        if not self.fast_parking():
            return False

        # exact parking
        if not self.exact_parking():
            if not self.fast_parking():
                return False
            if not self.exact_parking():
                return False

        # success
        return True

    def fast_parking(self):

        # fast parking
        accuracy_in_mm = 4
        max_step_count = 20

        # find parking sensor
        for i in range(max_step_count):
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')
            if self.y_filament_sensor_triggered():
                break

        # check parking success
        if not self.y_filament_sensor_triggered():
            return False

        # success
        return True
    
    def exact_parking(self):

        # exact parking
        accuracy_in_mm = 1
        max_step_count = 20

        # find parking sensor
        for n in range(max_step_count):
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E-' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')
            if not self.y_filament_sensor_triggered():
                break

        # check parking success
        if self.y_filament_sensor_triggered():
            return False

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Filament Positioning
    # -----------------------------------------------------------------------------------------------------------------------------
    def filament_positioning(self):

        # fast positioning
        if not self.fast_positioning():
            if not self.exact_positioning():
                return False

        # exact positioning
        if not self.exact_positioning():
            if not self.fast_positioning():
                return False
            if not self.exact_positioning():
                return False

        # success
        return True

    def fast_positioning(self):

        # fast positioning
        accuracy_in_mm = 4
        max_step_count = 20

        # find toolhead sensor
        for i in range(max_step_count):
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E-' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')
            if not self.toolhead_filament_sensor_triggered():
                break

        # check positioning success
        if self.toolhead_filament_sensor_triggered():
            return False

        # success
        return True
    
    def exact_positioning(self):

        # exact positioning
        accuracy_in_mm = 1
        max_step_count = 20

        # find toolhead sensor
        for n in range(max_step_count):
            self.gcode.run_script_from_command('G92 E0')
            self.gcode.run_script_from_command('G0 E' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.gcode.run_script_from_command('M400')
            if self.toolhead_filament_sensor_triggered():
                break

        # check positioning success
        if not self.toolhead_filament_sensor_triggered():
            return False

        # success
        return True

    # -----------------------------------------------------------------------------------------------------------------------------
    # Filament Caching
    # -----------------------------------------------------------------------------------------------------------------------------
    Filament_Groups = [[1,2],[4,5]]

    def cache_filament(self, filament):
        self.Filament_Cache[filament - 1] = True

    def uncache_all(self):
        self.respond("uncache_all " + str(self.Filament_Cache))
        for i in range(0, self.tool_count - 1):
            if self.Filament_Cache[i] == True:
                self.select_tool(i + 1)
                self.unload_filament_from_caching_position_to_reverse_bowden(i + 1)

    def uncache_filament(self, filament):
        self.Filament_Cache[filament - 1] = False

    def is_filament_cached(self, filament):
        if filament >= 0:
            return self.Filament_Cache[filament - 1]
        return False

    def is_cache_blocked(self, filament):
        filament_group = self.get_filament_group(filament)
        if filament_group >= 0:
            for f in range(0, len(self.Filament_Groups[filament_group])):
                if self.Filament_Groups[filament_group][f] != filament:
                    if self.is_filament_cached(self.Filament_Groups[filament_group][f]):
                        return self.Filament_Groups[filament_group][f]
        return -1

    def is_in_same_filament_group(self, new_filament, old_filament):
        return self.get_filament_group(new_filament) == self.get_filament_group(old_filament)

    def get_filament_group(self, filament):
        for g in range(0, len(self.Filament_Groups)):
            for f in range(0, len(self.Filament_Groups[g])):
                if self.Filament_Groups[g][f] == filament:
                    return g
        return -1

    # -----------------------------------------------------------------------------------------------------------------------------
    # Filament Sensor
    # -----------------------------------------------------------------------------------------------------------------------------
    def insert_gcode(self):
        self.respond("insert_gcode")

    def runout_gcode(self):
        self.respond("runout_gcode")

    # -----------------------------------------------------------------------------------------------------------------------------
    # Pause
    # -----------------------------------------------------------------------------------------------------------------------------
    Paused = False

    def pause_rome(self):
        self.Paused = True

        # enable heater timeout
        #if self.heater_timeout > 0:
        #    self.enable_heater_timeout()

        # call pause macro 
        self.gcode.run_script_from_command("_PAUSE_ROME IDLE_TIMEOUT=" + str(self.idle_timeout))

    def resume_rome(self):
        self.Paused = False

        # disable heater timeout
        if self.heater_timeout > 0:
            self.disable_heater_timeout()

        # go to last position
        if self.exchange_old_position != None:
            self.gcode.run_script_from_command('G0 Z' + str(self.exchange_old_position[2] + 2) + ' F3600')
            self.gcode.run_script_from_command('G0 X' + str(self.exchange_old_position[0]) + ' Y' + str(self.exchange_old_position[1]) + ' F3600')
            self.gcode.run_script_from_command('M400')

        # disable filament sensor
        self.disable_toolhead_filament_sensor()

        # resume print
        self.gcode.run_script_from_command("_RESUME_ROME")

    # -----------------------------------------------------------------------------------------------------------------------------
    # Helper
    # -----------------------------------------------------------------------------------------------------------------------------
    def stepper_move(self, stepper, dist, wait, speed, accel):
        stepper.do_move(dist, speed, accel, True)
        if wait:
            self.toolhead.wait_moves()      

    def stepper_homing_move(self, stepper, dist, wait, speed, accel, homing_move):
        stepper.do_homing_move(dist, speed, accel, homing_move > 0, abs(homing_move) == 1)
        if wait:
            self.toolhead.wait_moves()      

    def stepper_endstop_triggered(self, manual_stepper):
        endstop = manual_stepper.rail.get_endstops()[0][0]
        state = endstop.query_endstop(self.toolhead.get_last_move_time())
        return bool(state)

    def stepper_driver_status(self, stepper_name):
        driver_config = self.printer.lookup_object("tmc2209 manual_stepper " + stepper_name)
        return driver_config.get_status()

    def set_hotend_temperature(self, temp):
        
        # set hotend temperature
        if temp < self.heater.min_temp:
            self.respond("Selected temperature " + str(temp) + " too low, must be above " + str(self.heater.min_temp))
            return False
        if temp > self.heater.max_temp:
            self.respond("Selected temperature " + str(temp) + "too high, must be below " + str(self.heater.max_temp))
            return False
        if temp < self.heater.min_extrude_temp:
            self.respond("Selected temperature " + str(temp) + " below minimum extrusion temperature " + str(self.heater.min_extrude_temp))
            return False

        # start heating
        self.respond("Heat up nozzle to " + str(temp))
        self.extruder_set_temperature(temp, False)

        # success
        return True

    def respond(self, message):
        self.gcode.respond_raw(message)

    def toolhead_filament_sensor_triggered(self):
        return bool(self.toolhead_filament_sensor.runout_helper.filament_present)

    def y_filament_sensor_triggered(self):
        if self.Selected_Filament < 3:
            if self.y1_filament_sensor != None:
                return bool(self.y1_filament_sensor.runout_helper.filament_present)
        else:
            if self.y2_filament_sensor != None:
                return bool(self.y2_filament_sensor.runout_helper.filament_present)
        return False

    def enable_toolhead_filament_sensor(self):
        self.toolhead_filament_sensor.runout_helper.sensor_enabled = True

    def disable_toolhead_filament_sensor(self):
        self.toolhead_filament_sensor.runout_helper.sensor_enabled = False

    def extruder_set_temperature(self, temperature, wait):
        self.pheaters.set_temperature(self.heater, temperature, wait)

    def extruder_can_extrude(self):
        status = self.extruder.get_status(self.toolhead.get_last_move_time())
        result = status['can_extrude'] 
        return result

# -----------------------------------------------------------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------------------------------------------------------
def load_config(config):
    return ROME(config)

