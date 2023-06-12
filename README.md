#  ♈GIANO StealthBurner Dual Filament
   The ultimate filament loader.... 
   # This is a remake and adaptation of Rome https://github.com/HelgeKeck/rome for the StealthBurner 
   
![SB240_CW2_Integration_Mods v5 s](https://github.com/FBServiceTech3D/StealthBurner_Dual_Filament/assets/100725052/081aae14-c2aa-4962-996b-4d964c13f736) 

![SB240_CW2_Integration_Mods v5](https://github.com/FBServiceTech3D/StealthBurner_Dual_Filament/assets/100725052/18d93494-c014-4fdf-bae4-17164d7ce138)

# ⚙️Klipper Multi Extruder

A multi extruder to direct extruder solution for [Voron StealthBurner](https://vorondesign.com/voron_stealthburner) 

High speed multi material printing with as many extruders as you want

You can use any extruder you want. In this application we used two [Voron M4](https://vorondesign.com/voron_m4)

![images](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/aea0eff5-84b3-44d4-8cda-ef2a3eaf42ba)

# Intro: 

# Giano is MUCH faster then any regular MMU or ERCF setup. The whole filament unloading and loading process is multiple times faster, not only because Giano just has to park the filament behind the y-junction. In its native mode, Giano handles the loading and unloading process and skips the slicer controlled part of it. This process is highly optimized for a specific Hotend / Filament combination. No more configuration of cooling moves, skinnydip, ramming, ....

![SB240_CW2_Integration_Mods v12ok](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/b36b6050-b253-4a36-ac8f-50febbd1ff5b)


You can even set the acceleration for the wipe tower, in combination with the slicer max speed for the wipe tower feature, you can speed up the process even more.

With its Ooze Ex feature, it lets you use the most oozing hotends on the markets, it still produces a clean wipe tower

Every MM loading and unloading setting in the slicer will be deactivated and replaced with a simple unload macro.

![20230612_094937](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/89e8821c-249d-45aa-a637-c8b87efe3f90)

![20230612_095041](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/e810170a-40e0-4288-af72-0a2e702ae6d9)

![20230612_095047](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/3dc2fd88-93f9-49c9-8765-61148b4ee1a5)

# SuperSlicer configuration:

G-Code:
Printer Start G-code
GIANO_START_PRINT EXTRUDER_TEMP=[first_layer_temperature] BED_TEMP=[first_layer_bed_temperature] CHAMBER_TEMP=[chamber_temperature] TOOL=[initial_tool] WIPE_TOWER={wipe_tower} WIPE_TOWER_X={wipe_tower_x} WIPE_TOWER_Y={wipe_tower_y} WIPE_TOWER_WIDTH={wipe_tower_width} WIPE_TOWER_ROTATION_ANGLE={wipe_tower_rotation_angle} COOLING_TUBE_RETRACTION={cooling_tube_retraction} COOLING_TUBE_LENGTH={cooling_tube_length} PARKING_POS_RETRACTION={parking_pos_retraction} EXTRA_LOADING_MOVE={extra_loading_move}








Credits: Thanks to Voron team for all great work
         Thanks to HelgeKeck for all great work


