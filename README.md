# cordovaTools
















## Cordova Crosswalk Generator
  - USAGE:
```bash
xwalkgen [-h] [--fullscreen] [--landscape] bundle uid name
```
   Arguments:<br>
**bundle** = zip bundle cordova/crosswalk <br>
**uid** = package id <br>
**name** = project name
















## Plugme (Cordova Plugin Installer)
  - USAGE:
```bash
plugme (install, installdebug, remove, list, create) pluginfile/id  [-name Name] [-i] [-m Method1 ...N]
```
















Actions: <br>
**install** = Install plugin from zip/folder or plugin repository (github) <br>
**installdebug** = similar as above, but its install with verbose <br>
**remove** = remove installed plugin <br>
**list** = list of installed plugin <br>
**create** = create new plugin
















 Arguments: <br>
**pluginfile/id** = plugin file/folder or plugin repository (github) <br>
**-name** = (Optional) plugin name for created plugin <br>
**-i** = (Optional) indent size for created plugin. default =4 <br>
**-m** = (Optional) method for created plugin. you can add more




### Working with Android Terminal Emulator
  - Rooted Phone
  - Download [Terminal Emulator]( https://play.google.com/store/apps/details?id=jackpal.androidterm)
  - Download [QPython](https://play.google.com/store/apps/details?id=com.hipipal.qpyplus ), open and select Console, then close it
  - Download [Bash Shell](https://play.google.com/store/apps/details?id=com.bitcubate.android.bash.installer) and install bash




  - Create file under /sdcard with name .bash.rc, content:




```bash
export PYTHONHOME=/data/data/com.hipipal.qpyplus/files; export PYTHONPATH=/storage/sdcard0/com.hipipal.qpyplus/lib/python2.7/site-packages/:/data/data/com.hipipal.qpyplus/files/lib/python2.7/site-packages/:/data/data/com.hipipal.qpyplus/files/lib/python2.7/:/data/data/com.hipipal.qpyplus/files/lib/python27.zip:/data/data/com.hipipal.qpyplus/files/lib/python2.7/lib-dynload/;export PATH=$PATH:/sdcard/Android:/data/data/com.hipipal.qpyplus/files/bin;export LD_LIBRARY_PATH=.:/data/data/com.hipipal.qpyplus/files/lib/:/data/data/com.hipipal.qpyplus/files/:/data/data/com.hipipal.qpyplus/lib;
cd /sdcard;clear
```
  - Open Terminal Emulator, Goto Preferences and select Initial Command, type: *su -c "bash --init-file /sdcard/.bash.rc"*
  - Close Terminal Emulator
  - Copy plugme, plugme.py xwalkgen and xwalkgen.py to /sdcard/Android
  - Open Terminal Emulator, type *plugme* or *xwalkgen*, if you see  message "usage: blabla.." its work fine!!












Crafted by<br>
[Agus Ibrahim](http://fb.me/mynameisagoes)
