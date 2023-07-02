#!/bin/bash
# Made by Gab3d

echo "running Install.sh"

#check if  a symbolic link to the file ~/Giano_StealthBurner_Dual_Filament/Klipper_Extra/giano.py  in ~/klipper/klippy/extras/giano.py exist if not create it
if [ ! -L ~/klipper/klippy/extras/giano.py ]; then
    echo "Creating symbolic link to giano.py"
    ln -s ~/Giano_StealthBurner_Dual_Filament/Klipper_Extra/giano.py ~/klipper/klippy/extras/giano.py
fi
#check if  a symbolic link to the file ~/Giano_StealthBurner_Dual_Filament/Klipper_Macro/giano_macro.cfg  in ~/printer_data/config/giano_macro.cfg exist if not create it
if [ ! -L ~/printer_data/config/giano_macro.cfg ]; then
    echo "Creating symbolic link to giano_macro.cfg"
    ln -s ~/Giano_StealthBurner_Dual_Filament/Klipper_Macro/giano_macro.cfg ~/printer_data/config/giano_macro.cfg
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


#Check if the string includegiano exists in ~/printer_data/config/printer.cfg if not add the string includegiano on top of the file
if grep -q "[include giano.cfg]" ~/printer_data/config/printer.cfg; then
    echo "includegiano already in printer.cfg"
else
    echo "Adding includegiano to printer.cfg"
    sed -i '1s/^/[include giano.cfg]\n/' ~/printer_data/config/printer.cfg
fi

#Check if the string includegiano exists in ~/printer_data/config/printer.cfg if not add the string includegiano on top of the file
if grep -q "[include giano_marco.cfg]" ~/printer_data/config/printer.cfg; then
    echo "includegiano already in printer.cfg"
else
    echo "Adding includegiano to printer.cfg"
    sed -i '1s/^/[include giano_marco.cfg]\n/' ~/printer_data/config/printer.cfg
fi

#Check il the file giano.cfg exists in ~/printer_data/config/ if not copy it from ~/Giano_StealthBurner_Dual_Filament/Klipper_Config/giano.cfg
if [ ! -f ~/printer_data/config/giano.cfg ]; then
    echo "Copying giano.cfg to ~/printer_data/config/"
    cp ~/Giano_StealthBurner_Dual_Filament/Klipper_Config/giano.cfg ~/printer_data/config/giano.cfg
fi