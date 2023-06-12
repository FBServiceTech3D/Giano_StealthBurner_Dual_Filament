<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![GPL3][license-shield]][license-url]


![SB240_CW2_Integration_Mods v5 s](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/dd894760-e254-477b-895c-c986bd52fe40)


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament">
    <img src="IMG/logo.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">♈GIANO StealthBurner Dual Filament</h3>

  <p align="center">
    Klipper Multi Extruder

### A multi extruder to direct extruder solution for [Voron StealthBurner](https://vorondesign.com/voron_stealthburner)
    
    
 High speed multi material printing with as many extruders as you want
    <br />
    <a href="https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament">View Demo</a>
    ·
    <a href="https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/issues">Report Bug</a>
    ·
    <a href="https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/issues">Request Feature</a>
  </p>
</div>

![SB240_CW2_Integration_Mods v5](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/71da8862-c3a1-4655-9933-cf8a8ded5d64)


<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

![SB240_CW2_Integration_Mods v12s2](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/92ee60b2-31d3-4539-ade4-f49b9ec04bf2)


#### Giano is MUCH faster then any regular MMU or ERCF setup. The whole filament unloading and loading process is multiple times faster, not only because Giano just has to park the filament behind the y-junction. In its native mode, Giano handles the loading and unloading process and skips the slicer controlled part of it. This process is highly optimized for a specific Hotend / Filament combination. No more configuration of cooling moves, skinnydip, ramming, ....

![20230612_094937](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/f7bf3b83-7755-4c3e-8825-77db9a956970)

### Built With


## Getting Started

### Giano Modes

#### Giano can operate in two different modes, Native and Classic.

The Classic Mode works exactly like the MMU or ERCF. You are responsible to configure the Slicer like you would for the MMU or ERCF.

The Native Mode handles the filament loading and unloading on the Wipe tower. Faster filament changes, less Slicer configuration needed and more control over the process.

### SuperSlicer config for Native Mode:

![advanced](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/71b5662b-afeb-4c8f-84df-adf5e9ff9b40)

![capabilities](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/0809c041-d27d-4047-bd0f-899954224562)

![dip](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/afe13597-2fad-4c3e-b051-ca423245836b)

![toolchange_parameters](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/9e0a78d1-6c5e-463e-951f-1f6078d911ba)

![toolchange_temperature](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/3fa14829-5457-462c-9492-43322fdf9500)

![wipe_tower](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/0c1c1b70-eea7-4509-92d8-b18da7dae9c8)


### Prerequisites

#### SperSlicer Custom G-codes
* Giano Start Print G-Code
  ```sh
  GIANO_START_PRINT EXTRUDER_TEMP=[first_layer_temperature] BED_TEMP=[first_layer_bed_temperature] CHAMBER_TEMP=[chamber_temperature] TOOL=[initial_tool] WIPE_TOWER={wipe_tower} WIPE_TOWER_X={wipe_tower_x} WIPE_TOWER_Y={wipe_tower_y} WIPE_TOWER_WIDTH={wipe_tower_width} WIPE_TOWER_ROTATION_ANGLE={wipe_tower_rotation_angle} COOLING_TUBE_RETRACTION={cooling_tube_retraction} COOLING_TUBE_LENGTH={cooling_tube_length} PARKING_POS_RETRACTION={parking_pos_retraction} EXTRA_LOADING_MOVE={extra_loading_move}
  ```
* Giano END PRINT G-Code
  ```sh
  GIANO_END_PRINT
  ```
  
 * Giano Tool CHANGE G-Code
  ```sh
  CHANGE_TOOL TOOL=[next_extruder]
  ```  
  

###  Klipper Giano Installation

1. Clone this repo
``` shell
 cd ~
 git clone https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.git
```

2. Connect in ssh and run 

``` shell
 bash ~/Giano_StealthBurner_Dual_Filament/install.sh
```
3. Restarting klipper Giano will appear in your availabe updates

4. Configuration Update
Go in the configuration folder and update this values:
Motors update pin and current following your mcu instructions:
``` yaml

# -------------------------------------										
# Giano Extruder 1
# -------------------------------------										

[extruder_stepper giano_extruder_1]
extruder:
step_pin: PE6
dir_pin: !PA14
enable_pin: !PE0
microsteps: 64
rotation_distance: 22.6789511
full_steps_per_rotation: 200
gear_ratio: 80:20

[tmc2209 extruder_stepper giano_extruder_1]
uart_pin: PD3
run_current: 0.6
stealthchop_threshold: 0
interpolate: False
driver_TBL: 1
driver_TOFF: 3
driver_HEND: 9
driver_HSTRT: 7

# -------------------------------------										
# Giano Extruder 2
# M4 Voron
# -------------------------------------										
[extruder_stepper giano_extruder_2]
extruder:
step_pin: PE2
dir_pin: !PE3
enable_pin: !PD4
microsteps: 64
rotation_distance: 22.6789511
full_steps_per_rotation: 200
gear_ratio: 80:20

[tmc2209 extruder_stepper giano_extruder_2]
uart_pin: PE1
run_current: 0.6
stealthchop_threshold: 0
interpolate: False
driver_TBL: 1
driver_TOFF: 3
driver_HEND: 9
driver_HSTRT: 7


```

5. Adjust config 
#### Giano variables

| Name | Description |
| ---  | --- |
|heater_timeout: 6000                            | Heater Timeout in case of giano paused the print |
|unload_filament_after_print: 0                  | 0 = Filament remains in the hoted at print ends <br> 1 = unloads filament after printing has finished   |
|wipe_tower_acceleration: 5000                   | printer acceleration when printing the wipe tower  |
|use_ooze_ex: 1                                  | 1 = giano distributes oozed material over the length of the wipe tower  0 = try your luck  |
|use_filament_caching: 1                         | 1 = giano caches the filament right behind the toolhead sensor instead of completely unloading it <br>  0 = no caching |
|extruder_push_and_pull_test: 1                  | 1 = test if filament could successfully loaded into extruder <br>  0 = do not test |
|#filament_groups: 1:2,4:5                       | filament cache configuration, this tells giano which filament arrives in which bowden tube to the hotend |
|nozzle_loading_speed_mms: 10                    | extruder speed when moving the filament between the parking position and the nozzle |
|filament_homing_speed_mms: 50                   | extruder speed when moving the filament inside bowden tube |
|filament_parking_speed_mms: 50                  | extruder speed when moving the filament between the filament sensor and the parking position |
|parking_position_to_nozzle_mm: 50               | distance between the parking position and the nozzle |
|toolhead_sensor_to_bowden_cache_mm: 75          | distance between the filament sensor and the filament caching position |
|toolhead_sensor_to_bowden_parking_mm: 500       | distance between the filament sensor and the filament parking position |
|extruder_gear_to_parking_position_mm: 40        | distance between the extruder gears and the parking position |
|toolhead_sensor_to_extruder_gear_mm: 15         | distance between the filament sensor and the extruder gears |
|tool_count: 2                                   | number of feeding extruders, fixed 2 in case of Giano standard |
|giano_setup: 0                                  | 0 = multi extruder to direct extruder |



|<!-- USAGE EXAMPLES -->
## Usage

This is the list of gcodes availabe for Giano

### GCodes
`HOME_GIANO`  Hoomes both filament
`LOAD_TOOL`
`SELECT_TOOL`
`UNLOAD_TOOL`
`EJECT_TOOL`
`CHANGE_TOOL`
`GIANO_END_PRINT`
`GIANO_START_PRINT`
`GIANO_INSERT_GCODE`
`GIANO_RUNOUT_GCODE`
`LOAD_FILAMENTS`
`Z_HOME_TEST`
`F_RUNOUT`
`F_INSERT`
`SET_INFINITE_SPOOL`

### Customizable Macros included
`_UNLOAD_FROM_NOZZLE_TO_PARKING_POSITION`
`GIANO_LOAD_TOOL`
`GIANO_UNLOAD_TOOL`
`GIANO_SELECT_TOOL`
`GIANO_EJECT_TOOL`
`PAUSE_GIANO`
`RESUME_GIANO`
`LOAD_ALL_FILAMENTS`
`SET_INFINITE_SPOOL`
`_PAUSE_GIANO`
`_RESUME_GIANO`
`_SELECT_EXTRUDER`
`_EXTRUDER_SELECTED`
`_EXTRUDER_ERROR`
`_CONTINUE_PRINTING`
`_AUTOLOAD_RESUME_AFTER_INSERT`
`_INFINITE_RESUME_AFTER_SWAP`
`START_PRINT_GIANO`
`END_PRINT`
`_MOVE_AWAY`


<!-- ROADMAP -->
## Roadmap

- [x] Compliant and test 
- [ ] Beta test on Voron Italia group
- [ ] Public Release
    - [ ] Nested Feature

See the [open issues](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the GNU General Public License v3.0 License. See [`LICENSE`](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

- [FB ServiceTech 3d](https://linktr.ee/fbservicetech3d)
- GAB3D-[YouTube](https://www.youtube.com/@gab-3d) [GitHub](https://github.com/gab-3d/)

Project Link: [Giano_StealthBurner_Dual_Filament](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Project Rome](https://github.com/HelgeKeck/rome)
* []()
* []()

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.svg?style=for-the-badge



[contributors-url]: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.svg?style=for-the-badge
[forks-url]: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/network/members
[stars-shield]: https://img.shields.io/github/stars/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.svg?style=for-the-badge
[stars-url]: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/stargazers
[issues-shield]: https://img.shields.io/github/issues/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.svg?style=for-the-badge
[issues-url]: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/issues
[license-shield]: https://img.shields.io/github/license/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.svg?style=for-the-badge
[license-url]: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/blob/main/LICENSE
