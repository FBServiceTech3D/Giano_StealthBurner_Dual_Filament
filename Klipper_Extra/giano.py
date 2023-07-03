import time
from ssl import SSLSocket
from math import fabs
from re import T
import logging


class GIANO:
    Selected_Filament = -1
    Homed = False
    Filament_Cache = []
    Debug = 0
    
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

        gcode_macro = self.printer.load_object(config, 'gcode_macro')

        self.pre_unload_macro = gcode_macro.load_template(
            config, 'pre_unload_gcode', '')
        self.post_load_macro = gcode_macro.load_template(
            config, 'post_load_gcode', '')
        
        self.load_settings()
        self.register_commands()
        self.register_handle_connect()
    
    def load_settings(self):
        self.idler_stepper = None
        self.Filament_Cache = []
        self.tool_count = self.config.getint('tool_count', 2)
        self.Debug = self.config.getint('debug_level', 0)
        #The `Filament_Cache` list is used to keep track of whether or not each tool in the `giano` object has filament loaded.
        #The `for` loop iterates over each tool and appends a boolean value of `False` to the `Filament_Cache` list, indicating that no filament is currently loaded for that tool.
        for i in range(1, self.tool_count + 1):
            self.Filament_Cache.append(False)
        self.idle_timeout = self.config.getint('idle_timeout', 3600)
        self.unload_filament_after_print = self.config.getfloat('unload_filament_after_print', 1)
        self.runout_detected = False
        self.infinite_spool = False
        # Sets the `use_filament_caching` attribute based on the value. 
        # If the value is 1, `use_filament_caching` is set to True, otherwise it is set to False.
        if self.config.getfloat('use_filament_caching', 1) == 1:
            self.use_filament_caching = True
        else:
            self.use_filament_caching = False               
        
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

    def register_commands(self):
        self.gcode.register_command('G_LOAD_FILAMENTS', self.cmd_G_LOAD_FILAMENTS, desc=("G_LOAD_FILAMENTS"))
        self.gcode.register_command('G_CHANGE_TOOL', self.cmd_G_CHANGE_TOOL, desc=("G_CHANGE_TOOL"))
        for i in range(self.tool_count):
            self.gcode.register_command('T{}'.format(i),   self.cmd_G_SELECT_TOOL, desc=("G_SELECT_TOOL"))

        self.gcode.register_command('G_HOME', self.cmd_G_HOME, desc=("G_HOME"))
        self.gcode.register_command('G_EJECT', self.cmd_G_EJECT, desc=("G_EJECT"))

        self.gcode.register_command('Z_HOME_TEST', self.cmd_Z_HOME_TEST, desc=("Z_HOME_TEST"))
    
    # cmd implementation
    def cmd_Z_HOME_TEST(self,param):
        #self.respond(str(dir(self.pre_unload_macro.gcode)))
        self.pre_unload_macro.run_gcode_from_command()
        return True


    def cmd_G_HOME(self, param):
        if not self.Homed:
            if not self.home():
                return False
        if not self.home_extruder_filaments():
            return False
        return True

    def cmd_G_EJECT(self, param):
        if self.toolhead_filament_sensor_triggered():
            self.unload_tool(-1, False)
        if self.use_filament_caching:
            self.uncache_all()     
        self.Homed = False


    def cmd_G_SELECT_TOOL(self, param):
        tool = int(param.get_command().partition('T')[2])
        self.respond("Tool :" + str(tool) + " selected")
        if not self.change_tool(tool):
            self.pause_giano()

    def cmd_G_LOAD_FILAMENTS(self, param):
        if not self.Homed:
            if not self.home():
                return False
        if not self.home_extruder_filaments():
            return False
        return True
    def cmd_G_CHANGE_TOOL(self, param):
        tool = param.get_int('TOOL', None, minval=0, maxval=self.tool_count)
        if not self.change_tool(tool):
            self.pause_giano()
    # -----------------------------------------------------------------------------------------------------------------------------
    # Home Extruder Feeder
    # -----------------------------------------------------------------------------------------------------------------------------
    def home(self):
        if self.Debug>0: self.respond("home")
        # homing giano
        self.respond("Homing Giano!")
        self.Homed = False
        self.Paused = False

        # precheck
        if not self.can_home():
            return False
   
        # success
        self.Homed = True
        self.Selected_Filament = -1
        self.respond("Welcome Home Giano!")
        return True

    def can_home(self):
        if self.Debug>0: self.respond("can_home")
        # check hotend temperature
        if not self.extruder_can_extrude():
            self.respond("Preheat Nozzle in order to Home Giano!" + "-129")
            return False

        # check filament sensor
        # unload filament from nozzle
        if self.toolhead_filament_sensor_triggered():
            self.respond("Sensor triggered unload")
            if not self.unload_tool(-1, False):
                self.respond("Can not unload from nozzle!" + "-136")
                #add a response with row number

                
                return False


        # check
        if self.toolhead_filament_sensor_triggered():
            self.respond("Filament stuck in extruder!")
            return False

        # success
        return True
    def home_extruder_filaments(self):
        if self.Debug>0: self.respond("home_extruder_filaments")
        # home all filaments
        for i in range(1, self.tool_count + 1):
            if not self.home_extruder_filament(i):
                return False

        # success
        return True
    
    def home_extruder_filament(self, filament):
        if self.Debug>0: self.respond("home_extruder_filament filament:" + str(filament))
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

    

    def select_tool(self, tool=-1):
        if self.Debug>0: self.respond("select_tool tool:" + str(tool))
    
        # This code selects a specific tool by calling the `select_tool_extruder_feeder` method with the specified `tool` parameter. 
        # If `tool` is 0, all tools are unselected. If `tool` is -1, all tools are selected. 
        # The `Selected_Filament` attribute of the `giano` object is set to the selected tool.
        # A response message is sent to indicate which tool was selected or unselected. 
        # The `unselect_tool_extruder_feeder` method is called to unselect any previously selected tool.
        if tool == 0:
            self.respond("unselecting tools")
        elif tool == -1:
            self.respond("selecting all tools")
        else:
            self.respond("selecting tool " + str(tool))
        self.unselect_tool_extruder_feeder()
        self.select_tool_extruder_feeder(tool)

        self.Selected_Filament = tool
        self.respond("tool " + str(tool) + " selected")
    
    def select_tool_extruder_feeder(self, tool):
        if self.Debug>0: self.respond("select_tool_extruder_feeder tool:" + str(tool))
        # This code selects a specific tool by running a G-code script to synchronize the extruder motion.
        # The `tool` parameter specifies the tool to select, and if it is set to -1, all tools are selected. 
        # The `for` loop iterates over each tool and runs the G-code script for the specified tool. 
        # The `giano_extruder_X` parameter specifies the extruder to synchronize, where X is the tool number. 
        # The `MOTION_QUEUE` parameter specifies the motion queue to use for the extruder.
        if tool != 0:
            for i in range(1, self.tool_count + 1):

                if tool == i or tool == -1:
                    self.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=giano_extruder_' + str(i) + ' MOTION_QUEUE=extruder')
  
    def unselect_tool_extruder_feeder(self):
        if self.Debug>0: self.respond("unselect_tool_extruder_feeder")
        self.Selected_Filament = -1
        self.respond("Looping and remove synced extruders")
        for i in range(1, self.tool_count + 1):
            self.run_script_from_command('SYNC_EXTRUDER_MOTION EXTRUDER=giano_extruder_' + str(i) + ' MOTION_QUEUE=')
# -----------------------------------------------------------------------------------------------------------------------------
# Load Filament
# -----------------------------------------------------------------------------------------------------------------------------
    def load_filament_from_reverse_bowden_to_toolhead_sensor(self, exact_positioning=True):
        if self.Debug>0: self.respond("load_filament_from_reverse_bowden_to_toolhead_sensor")

        # set load distance

        
        load_distance = self.toolhead_sensor_to_bowden_cache_mm

        # filament caching
        is_cached = False
        
        self.respond("Filament " + str(self.Selected_Filament) + " selected!")
        
        if not self.toolhead_filament_sensor_triggered():
            # initial move
            self.run_script_from_command('G92 E0')
            if self.Debug>0: self.respond("E toolhead_sensor_to_bowden_cache_mm("+str(load_distance)+") F filament_homing_speed_mms * 60")
            self.run_script_from_command('G0 E' + str(load_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.run_script_from_command('M400')
        else:
             self.respond("Sensor is already triggered before first move...")
             return False

        # try to find the sensor
        self.respond("try to find the sensor...")
        step_distance = 20
        max_step_count = 50
        if not self.toolhead_filament_sensor_triggered():
            for i in range(max_step_count):
                #self.respond("Reaching the sensor move:" + str(i))
                self.run_script_from_command('G92 E0')
                if self.Debug>0: self.respond("E step_distance("+str(step_distance)+") F filament_homing_speed_mms * 60")
                self.run_script_from_command('G0 E' + str(step_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
                self.run_script_from_command('M400')
                if self.toolhead_filament_sensor_triggered():
                    self.respond("Sensor found at move:" + str(i))
                    break
        else:
            self.respond("Sensor is already triggered...")
        
        # check if sensor was found
        self.respond("Double checking if sensor was found...")
        if not self.toolhead_filament_sensor_triggered():
            self.respond("Could not find filament sensor!")
            return False
        else:
            self.respond("Sensor found")

        # exact positioning
        if exact_positioning == True:
            self.respond("Proceed with exact positioning...")
            if not self.filament_positioning():
                self.respond("Could not position the filament in the filament sensor for exact positioning!")
                return False

        # success
        return True

    def load_filament_from_toolhead_sensor_to_parking_position(self):
        if self.Debug>0: self.respond("load_filament_from_toolhead_sensor_to_parking_position")

        # move filament to parking position
        self.run_script_from_command('G92 E0')
        if self.Debug>0: self.respond("E toolhead_sensor_to_extruder_gear_mm("+str(self.toolhead_sensor_to_extruder_gear_mm)+") + extruder_gear_to_parking_position_mm("+str(self.extruder_gear_to_parking_position_mm)+") ) F filament_parking_speed_mms")
        self.run_script_from_command('G0 E' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm) + ' F' + str(self.filament_parking_speed_mms * 60))
        self.run_script_from_command('M400')

        # extruder push and pull test
        if self.extruder_push_and_pull_test:
            push_and_pull_offset = 10
            self.run_script_from_command('G92 E0')
            if self.Debug>0: self.respond("E- toolhead_sensor_to_extruder_gear_mm("+str(self.toolhead_sensor_to_extruder_gear_mm)+") + extruder_gear_to_parking_position_mm("+str(self.extruder_gear_to_parking_position_mm)+") - push_and_pull_offset("+str(push_and_pull_offset)+") F filament_parking_speed_mms")
            self.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset) + ' F' + str(self.filament_parking_speed_mms * 60))
            self.run_script_from_command('M400')
            if not self.toolhead_filament_sensor_triggered():
                self.respond("could not load filament into extruder!")
                return False
            self.run_script_from_command('G92 E0')
            if self.Debug>0: self.respond("E toolhead_sensor_to_extruder_gear_mm("+str(self.toolhead_sensor_to_extruder_gear_mm)+") + extruder_gear_to_parking_position_mm("+str(self.extruder_gear_to_parking_position_mm)+") - push_and_pull_offset("+str(push_and_pull_offset)+") F filament_parking_speed_mms")
            self.run_script_from_command('G0 E' + str(self.toolhead_sensor_to_extruder_gear_mm + self.extruder_gear_to_parking_position_mm - push_and_pull_offset) + ' F' + str(self.filament_parking_speed_mms * 60))
            self.run_script_from_command('M400')

        # success
        return True

    def load_filament_from_parking_position_to_nozzle(self):
        if self.Debug>0: self.respond("load_filament_from_parking_position_to_nozzle")

        # load filament into nozzle
        self.run_script_from_command('G92 E0')
        if self.Debug>0: self.respond("E parking_position_to_nozzle_mm("+str(self.parking_position_to_nozzle_mm)+") F nozzle_loading_speed_mms")
        self.run_script_from_command('G0 E' + str(self.parking_position_to_nozzle_mm) + ' F' + str(self.nozzle_loading_speed_mms * 60))

        self.run_script_from_command('G4 P1000')
        self.run_script_from_command('G92 E0')
        self.run_script_from_command('M400')

        # success
        return True
    
    # -----------------------------------------------------------------------------------------------------------------------------
    # Change Tool
    # -----------------------------------------------------------------------------------------------------------------------------
    
    Filament_Changes = 0


    

    def change_tool(self, tool):
        self.respond("change_tool " + str(tool + 1) + " number of changes: " + str(self.Filament_Changes) + " Selected_Filament: " + str(self.Selected_Filament))
        if (self.Selected_Filament == tool+1):
            self.respond("Tool " + str(tool+1) + " already selected!")
            return True
        else:
            # change tool
            #if self.Filament_Changes > 0:
            if self.Filament_Changes>0: self.before_change()
            if not self.load_tool(tool + 1, self.use_filament_caching):

                # send notification
                #self.run_script_from_command('_EXTRUDER_ERROR EXTRUDER=' + str(tool))

                return False
            self.after_change()
            self.Filament_Changes = self.Filament_Changes + 1

            # success
            return True

    def load_tool(self, tool,  cache):
        logging.info("load_tool " + str(tool))
        if self.Debug>0: self.respond("load_tool tool: " + str(tool))
        
        # send notification
        # self.run_script_from_command('_SELECT_EXTRUDER EXTRUDER=' + str(tool))

        # home if not homed yet
        if not self.Homed:
            self.respond("Not homed")
            if not self.home():
                return False
        else:
            self.respond("Already homed")

        # check hotend temperature
        if not self.extruder_can_extrude():
            self.respond("Hotend too cold! stopping filament change")
            return False

        # enable filament sensor
        self.enable_toolhead_filament_sensor()

        # load filament
        if self.toolhead_filament_sensor_triggered():
            if not self.unload_tool(tool, cache):
                self.respond("could not unload tool!")
                return False
        # else:
        #     self.respond("Possible sensor failure!")
        #     self.respond("Filament sensor should be triggered but it isnt!")
        #     return False

        self.select_tool(tool)
        if not self.load_filament_from_reverse_bowden_to_toolhead_sensor():
            self.respond("could not load tool to sensor!")
            return False
        if not self.load_filament_from_toolhead_sensor_to_parking_position():
            return False
        if not self.load_filament_from_parking_position_to_nozzle():
            self.respond("could not load into nozzle!")
            return False

        # success
        self.respond("tool " + str(tool) + " loaded")

        # send notification
        #self.run_script_from_command('_EXTRUDER_SELECTED EXTRUDER=' + str(tool))

        return True

    def unload_tool(self, new_filament, cache):
        if self.Debug>0: self.respond("unload_tool new_filament: " +str(new_filament))
        if self.Debug>0: self.respond("Selected filament:" +str(self.Selected_Filament))
        # select tool
        self.select_tool(self.Selected_Filament)

        
        if not self.unload_filament_from_parking_position_to_toolhead_sensor():
            return False
        if not self.unload_filament_from_toolhead_sensor(new_filament, cache):
            return False

        # success
        return True
    def uncache_all(self):
        if self.Debug>0: self.respond("uncache_all " + str(self.Filament_Cache))
        for i in range(0, self.tool_count - 1):
            if self.Filament_Cache[i] == True:
                self.select_tool(i + 1)
                self.unload_filament_from_caching_position_to_reverse_bowden(i + 1)
        
    def before_change(self):
        if self.Debug>0: self.respond("Before change")
        self.pre_unload_macro.run_gcode_from_command()
        return True
        
    def after_change(self):
        if self.Debug>0: self.respond("After change")
        self.post_load_macro.run_gcode_from_command()
        self.disable_toolhead_filament_sensor()

        # send notification
        #self.run_script_from_command('_CONTINUE_PRINTING EXTRUDER=' + str(self.Selected_Filament))

# -----------------------------------------------------------------------------------------------------------------------------
# Unload Filament
# -----------------------------------------------------------------------------------------------------------------------------
    ## This code unloads filament from the toolhead sensor by ejecting the filament and moving the extruder motor back to the bowden parking position. 
    #  The `new_filament` parameter specifies the ID of the new filament to load, and the `cache` parameter specifies whether or not to cache the filament.
    #  The `unload_distance` variable is set to the distance between the toolhead sensor and the bowden cache in millimeters. 
    #  The `is_cached` variable is set to False to indicate that the filament has not been cached yet.
    #  If the filament is ejected successfully, the `uncache_filament` method is called to uncache the filament. 
    #  The method returns `True` if the filament is unloaded successfully, otherwise it returns `False`.

    def unload_filament_from_toolhead_sensor(self, new_filament, cache):
        if self.Debug>0: self.respond("unload_filament_from_toolhead_sensor")
        if self.Debug>0: self.respond("new_filament " + str(new_filament))

        # set unload distance
        unload_distance = self.toolhead_sensor_to_bowden_parking_mm

        # eject filament
        self.run_script_from_command('G92 E0')
        if self.Debug>0: self.respond("E- toolhead_sensor_to_bowden_parking_mm("+str(self.toolhead_sensor_to_bowden_parking_mm)+") F filament_homing_speed_mms * 60")
        self.run_script_from_command('G0 E-' + str(unload_distance) + ' F' + str(self.filament_homing_speed_mms * 60))
        self.run_script_from_command('M400')

        # check if filament is ejected from toolhead
        if self.toolhead_filament_sensor_triggered():
            return False

        # uncache filament
        self.uncache_filament(self.Selected_Filament)

        # success
        return True
    
    def unload_filament_from_caching_position_to_reverse_bowden(self, filament):
        if self.Debug>0: self.respond("unload_filament_from_caching_position_to_reverse_bowden filament:" +str(filament) )
        
        # select filament
        self.select_tool(filament)

        # eject filament
        self.run_script_from_command('G92 E0')
        if self.Debug>0: self.respond("E- toolhead_sensor_to_bowden_parking_mm("+str(self.toolhead_sensor_to_bowden_parking_mm)+") - toolhead_sensor_to_bowden_cache_mm("+str(self.toolhead_sensor_to_bowden_cache_mm)+") F filament_homing_speed_mms * 60")
        self.run_script_from_command('G0 E-' + str(self.toolhead_sensor_to_bowden_parking_mm - self.toolhead_sensor_to_bowden_cache_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
        self.run_script_from_command('M400')

        # check if filament is ejected
        if self.toolhead_filament_sensor_triggered():
            self.respond("Filament sensor still triggered after unloading! unload_filament_from_caching_position_to_reverse_bowden")
            return False

        
        self.uncache_filament(self.Selected_Filament)

        # success
        return True


    # -----------------------------------------------------------------------------------------------------------------------------
    # Filament Positioning
    # -----------------------------------------------------------------------------------------------------------------------------
    def filament_positioning(self):
        if self.Debug>0: self.respond("filament_positioning")
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
        if self.Debug>0: self.respond("fast_positioning")
        # fast positioning
        accuracy_in_mm = 4
        max_step_count = 20

        # find toolhead sensor
        for i in range(max_step_count):
            self.run_script_from_command('G92 E0')
            if self.Debug>0: self.respond("E- accuracy_in_mm("+str(accuracy_in_mm)+") F filament_homing_speed_mms * 60")
            self.run_script_from_command('G0 E-' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.run_script_from_command('M400')
            if not self.toolhead_filament_sensor_triggered():
                break

        # check positioning success
        if self.toolhead_filament_sensor_triggered():
            return False

        # success
        return True
    
    def exact_positioning(self):
        if self.Debug>0: self.respond("exact_positioning")
        # exact positioning
        accuracy_in_mm = 1
        max_step_count = 20

        # find toolhead sensor
        for n in range(max_step_count):
            self.run_script_from_command('G92 E0')
            if self.Debug>0: self.respond("E accuracy_in_mm("+str(accuracy_in_mm)+") F filament_homing_speed_mms * 60")
            self.run_script_from_command('G0 E' + str(accuracy_in_mm) + ' F' + str(self.filament_homing_speed_mms * 60))
            self.run_script_from_command('M400')
            if self.toolhead_filament_sensor_triggered():
                break

        # check positioning success
        if not self.toolhead_filament_sensor_triggered():
            return False

        # success
        return True
    def unload_filament_from_parking_position_to_toolhead_sensor(self):
        self.respond("unload_filament_from_parking_position_to_toolhead_sensor")
        
        # unload filament to toolhead sensor
        self.run_script_from_command('G92 E0')
        self.run_script_from_command('M400')
        if self.Debug>0: self.respond("E- extruder_gear_to_parking_position_mm("+str(self.extruder_gear_to_parking_position_mm)+") + toolhead_sensor_to_extruder_gear_mm("+str(self.toolhead_sensor_to_extruder_gear_mm)+") F filament_parking_speed_mms * 60")
        self.run_script_from_command('G0 E-' + str(self.extruder_gear_to_parking_position_mm + self.toolhead_sensor_to_extruder_gear_mm) + ' F' + str(self.filament_parking_speed_mms * 60))
  
        self.run_script_from_command('M400')

        # success
        return True
############################################################################################################################################################################
# Helpers
############################################################################################################################################################################
    def run_script_from_command(self,cmd):
        if self.Debug>1:
            if cmd[0:4] == "G0 E":
                self.respond(cmd)
        if self.Debug>2: self.respond(cmd)
        self.gcode.run_script_from_command(cmd)
        
    def respond(self, message):
        self.gcode.respond_raw(message)

    def extruder_can_extrude(self):
        
        status = self.extruder.get_status(self.toolhead.get_last_move_time())
        result = status['can_extrude'] 
        if self.Debug>0: self.respond("extruder_can_extrude status: " + str (result))
        return result

    def toolhead_filament_sensor_triggered(self):
        if self.Debug>0: self.respond("toolhead_filament_sensor_triggered triggered:"+ str(bool(self.toolhead_filament_sensor.runout_helper.filament_present)))
        return bool(self.toolhead_filament_sensor.runout_helper.filament_present)
    
    def uncache_filament(self, filament):
        if self.Debug>0: self.respond("uncache_filament")
        self.Filament_Cache[filament - 1] = False

    def enable_toolhead_filament_sensor(self):
        if self.Debug>0: self.respond("enable_toolhead_filament_sensor")
        self.toolhead_filament_sensor.runout_helper.sensor_enabled = True
    
    def disable_toolhead_filament_sensor(self):
        if self.Debug>0: self.respond("disable_toolhead_filament_sensor")
        self.toolhead_filament_sensor.runout_helper.sensor_enabled = False

    # -----------------------------------------------------------------------------------------------------------------------------
    # Pause
    # -----------------------------------------------------------------------------------------------------------------------------
    Paused = False

    def pause_giano(self):
        self.Paused = True

        # enable heater timeout
        #if self.heater_timeout > 0:
        #    self.enable_heater_timeout()

        # call pause macro 
        self.run_script_from_command("_PAUSE_GIANO IDLE_TIMEOUT=" + str(self.idle_timeout))

# -----------------------------------------------------------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------------------------------------------------------
def load_config(config):
    return GIANO(config)