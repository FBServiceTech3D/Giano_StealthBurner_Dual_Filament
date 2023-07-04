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

## _Work in progress under development_

![SB240_CW2_Integration_Mods v5 s](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/1db03bbf-cca7-4887-9c1b-d4e300a5cdfb)


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

![SB240_CW2_Integration_Mods v5](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/3393defb-127d-405b-8dff-4e08acb12b1d)


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

![SB240_CW2_Integration_Mods v13ff](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/5cff657e-e45d-4f0c-9d16-cf6a58ec48fd)

[PDF DOC.pdf](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/files/11733058/PDF.DOC.pdf)

#### Giano, first of all, is a remix of the existing [Rome project](https://github.com/HelgeKeck/rome). We just managed to integrate it into the Voron StealthBurner tolhead and simplified for the specific Voron use 
Giano is MUCH faster then any regular MMU or ERCF setup. The whole filament unloading and loading process is multiple times faster, not only because Giano just has to park the filament behind the y-junction. In its native mode, Giano handles the loading and unloading process and skips the slicer controlled part of it. This process is highly optimized for a specific Hotend / Filament combination. No more configuration of cooling moves, skinnydip, ramming, ....
 

![20230612_094937](https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament/assets/100725052/b98e392d-cd3b-4dc0-9ac5-88c44e93fbab)


### Built With


## Getting Started

Giano is super simple: 
- You can call `GIANO_HOME` to position the filaments near the toolheads _not required_
-  You can use `T0` or `GIANO_FILAMENT_1` to select the first filament.
-  You can use `T1` or `GIANO_FILAMENT_2` to select the second filament.
-  You can use `EJECT_TOOL` In the print end to unload the filament


No special slicer configuration a required, only classic MMU Setup.

No special start gcode or end gcode

In the file giano_bambu.cfg you can see the macro I use to avoid purge tower like in this [video](https://youtube.com/shorts/Jlu3IUiA1i4).

Thanks ERCF for the tip macr

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
|use_filament_caching: 1                         | 1 = giano caches the filament right behind the toolhead sensor instead of completely unloading it <br>  0 = no caching |
|extruder_push_and_pull_test: 1                  | 1 = test if filament could successfully loaded into extruder <br>  0 = do not test |
| ---  | --- |
|nozzle_loading_speed_mms: 10                    | extruder speed when moving the filament between the parking position and the nozzle |
|filament_homing_speed_mms: 50                   | extruder speed when moving the filament inside bowden tube |
|filament_parking_speed_mms: 50                  | extruder speed when moving the filament between the filament sensor and the parking position |
| ---  | --- |
|parking_position_to_nozzle_mm: 50               | distance between the parking position and the nozzle |
|toolhead_sensor_to_bowden_cache_mm: 75          | distance between the filament sensor and the filament caching position |
|toolhead_sensor_to_bowden_parking_mm: 500       | distance between the filament sensor and the filament parking position |
|extruder_gear_to_parking_position_mm: 40        | distance between the extruder gears and the parking position |
|toolhead_sensor_to_extruder_gear_mm: 15         | distance between the filament sensor and the extruder gears |
| ---  | --- |
|tool_count: 2                                   | number of feeding extruders, fixed 2 in case of Giano standard |
|debug_level|0 no debug, 1 normal, 2 verbose, 3 All commands|
| ---  | --- |
|pre_unload_gcode|This occurs before the unload call - usefull to move to a parking location and or make a filament tip|
|post_load_gcode|This occurs after the filament change - usefull to purge, clean the nozzel and return to previous state|


|<!-- USAGE EXAMPLES -->
## Usage

This is the list of gcodes availabe for Giano

### GCodes
- `HOME_GIANO` - Hoomes both filament
- `GIANO_LOAD_ALL_FILAMENTS`- Similar to home, home both filaments
- `EJECT_TOOL` - Eject from nozzle all filaments
- `GIANO_FILAMENT_1` - Select filament 1 
- `GIANO_FILAMENT_2` - Select filament 2

### Customizable Macros 
- `_PAUSE_GIANO` occurs when giano encounter an error
- `_RESUME_GIANO` resume printing

### Customizable movemets 
- `pre_unload_gcode` - This occurs before the unload call - usefull to move to a parking location and or make a filament tip
- `post_load_gcode` - This occurs after the filament change - usefull to purge, clean the nozzel and return to previous state



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
* [Voron Stealthburner](https://github.com/VoronDesign/Voron-Stealthburner)
* ([EnragedRabbitProject](https://github.com/EtteGit/EnragedRabbitProject/tree/main)
  

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
