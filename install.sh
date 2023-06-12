#!/bin/bash
# Made by Gab3d

echo "running Install.sh"

#check if  a symbolic link to the file ~/Giano_StealthBurner_Dual_Filament/Klipper Extra/giano.py  in ~/klipper/klippy/extras/giano.py exist if not create it
if [ ! -L ~/klipper/klippy/extras/giano.py ]; then
    echo "Creating symbolic link to giano.py"
    ln -s ~/Giano_StealthBurner_Dual_Filament/Klipper_Extra/giano.py ~/klipper/klippy/extras/giano.py
fi

#check if the string 'Giano_StealthBurner_Dual_Filament.git' exists in the file ~/printer_data/config/moonraker.conf
if grep -q "Giano_StealthBurner_Dual_Filament.git" ~/printer_data/config/moonraker.conf; then
    echo "Giano_StealthBurner_Dual_Filament.git already in moonraker.conf"
else
    echo "Adding Giano_StealthBurner_Dual_Filament.git to moonraker.conf"
echo  "

[update_manager Giano_StealthBurner_Dual_Filament]
type: git_repo
channel: beta
primary_branch: main
path: ~/Giano_StealthBurner_Dual_Filament
managed_services:
    klipper
    moonraker
origin: https://github.com/FBServiceTech3D/Giano_StealthBurner_Dual_Filament.git
install_script: install.sh
    " >> ~/printer_data/config/moonraker.conf
fi

#check if the string 'Giano_StealthBurner_Dual_Filament' exists in the file ~/printer_data/config/printer.cfg
if grep -q "Giano_StealthBurner_Dual_Filament" ~/printer_data/config/printer.cfg; then
    echo "Giano_StealthBurner_Dual_Filament already in printer.cfg"
else
    echo "Adding Giano_StealthBurner_Dual_Filament to printer.cfg"

#copy Klipper_Macro/giano.cfg to ~/printer_data/config/
cp ~/Giano_StealthBurner_Dual_Filament/Klipper_Macro/giano.cfg ~/printer_data/config/

echo  "
# Giano_StealthBurner_Dual_Filament
[include giano.cfg]
" >> ~/printer_data/config/printer.cfg
fi