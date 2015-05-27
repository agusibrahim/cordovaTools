"""
XWalkBuilder
Crosswalk Cordova Generator for Android
Author:      Agus Ibrahim
Created:     26/05/2015
Copyright:   (c) Agus Ibrahim 2015

USAGE:
    xwalkgen <CrosswalkZipBundle> <PackageId> <ProjectName>
OR
import xwalkgen
xwalk = xwalkgen.XWalkbuilder("CrosswalkBundle.zip")
xwalk.make("id.agusibrahim.myapps", "AplikasiSaya", "fullscreen", "landscape")

Follow @agusmibrahim
"""
from zipfile import ZipFile, is_zipfile
from os import path, getcwd, listdir, makedirs, remove
import re
import sys
import shutil


class NotZipFile(Exception):
    pass


class NotXWalkBundle(Exception):
    pass


class PackageIDError(Exception):
    pass
pwd = getcwd()


class ziputil:

    def __init__(self): pass

    def extract(self, src, target, onself=0, xmls=None):
        if not xmls:
            ns = self.namelist
            jipo = self.zipo
        else:
            ns = xmls.namelist()
            jipo = xmls
        for f in ns:
            if f.startswith(src):
                fn = path.basename(f)
                dn = path.dirname(f)[len(src):]
                if sys.platform == "win32":
                    dn = dn.replace("/", "\\")
                if fn:
                    raw_src = jipo.read(f)
                    root = path.basename(src)
                    if src.endswith("/"):
                        root = path.basename(src[:-1])
                    if src.endswith("/"):
                        if not onself:
                            target_fix = path.join(target, root, dn)
                        else:
                            target_fix = path.join(target, dn)
                    else:
                        target_fix = path.join(target, dn)

                    if not path.exists(target_fix) and src.endswith("/"):
                        makedirs(target_fix)
                    if src.endswith("/"):
                        open(path.join(target_fix, fn), "w").write(raw_src)
                    else:
                        if onself:
                            open(target, "w").write(raw_src)
                        else:
                            if not path.exists(target_fix):
                                makedirs(target_fix)
                            open(path.join(target_fix, fn), "w").write(raw_src)
Extract = ziputil().extract


class XWalkbuilder:

    def __init__(self, zipbundle):
        if is_zipfile(zipbundle):
            self.zwalk = ZipFile(zipbundle)
            self.nl = self.zwalk.namelist()
            xdet = re.findall(
                "^crosswalk-cordova-([\w\.-]*)-(\w*)/$", self.nl[0])
            if not xdet and not re.match("^cordova-android-(.*?)/$", self.nl[0]):
                raise NotXWalkBundle(
                    "Bukan Crosswalk Cordova bundle, silahkan download di http://crosswalk-project.com")
        else:
            raise NotZipFile("Bukan file zip")

    def make(self, uid, name, screen="normal", orientation="potrait", apilevel="21", nonxwalk=False):
        if not screen.lower() in ["normal", "fullscreen"]:
            screen = "normal"
        if not orientation.lower() in ["potrait", "landscape"]:
            orientation = "potrait"
        if not re.match("^[a-zA-Z0-9-_\. ]*$", name):
            raise NameError("Nama tidak valid")
        if not re.match("^[a-z][a-z0-9]*\.[a-z0-9\.]*$", uid):
            raise PackageIDError("Package ID tidak valid")
        proj = path.join(pwd, name)
        tmplocation = self.nl[0] + "bin/templates/project/"
        makedirs(proj)
        manifest = self.zwalk.read(tmplocation + "AndroidManifest.xml").replace(
            "__PACKAGE__", uid).replace("__ACTIVITY__", "MainActivity").replace("__APILEVEL__", apilevel)
        activity = self.zwalk.read(
            tmplocation + "Activity.java").replace("__ID__", uid).replace("__ACTIVITY__", "MainActivity")
        iconraw = self.zwalk.read(tmplocation + "res/drawable/icon.png")
        strings = self.zwalk.read(
            tmplocation + "res/values/strings.xml").replace("__NAME__", name)
        config = 'PHdpZGdldCBpZD0iaW8uY29yZG92YS5oZWxsb0NvcmRvdmEiIHZlcnNpb249IjIuMC4wIiB4bWxu\ncz0iaHR0cDovL3d3dy53My5vcmcvbnMvd2lkZ2V0cyI+Cgk8bmFtZT5IZWxsbyBDb3Jkb3ZhPC9u\nYW1lPgoJPGRlc2NyaXB0aW9uPgoJCUEgc2FtcGxlIEFwYWNoZSBDb3Jkb3ZhIGFwcGxpY2F0aW9u\nLiBHZW5lcmF0ZWQgYnkgQWd1cyBJYnJhaGltIHwgQGFndXNtaWJyYWhpbQoJPC9kZXNjcmlwdGlv\nbj4KCTxhdXRob3IgZW1haWw9Im15bmFtZWlzYWdvZXNAZmFjZWJvb2suY29tIiBocmVmPSJodHRw\nOi8vZmIubWUvbXluYW1laXNhZ29lcyI+CgkJQWd1cyBJYnJhaGltCgk8L2F1dGhvcj4KCTxhY2Nl\nc3Mgb3JpZ2luPSIqIiAvPgoJPGNvbnRlbnQgc3JjPSJpbmRleC5odG1sIiAvPgoJPHByZWZlcmVu\nY2UgbmFtZT0ibG9nbGV2ZWwiIHZhbHVlPSJERUJVRyIgLz4KCTxwcmVmZXJlbmNlIG5hbWU9InVz\nZUJyb3dzZXJIaXN0b3J5IiB2YWx1ZT0idHJ1ZSIgLz4KCTxwcmVmZXJlbmNlIG5hbWU9ImV4aXQt\nb24tc3VzcGVuZCIgdmFsdWU9ImZhbHNlIiAvPgoJPHByZWZlcmVuY2UgbmFtZT0ic2hvd1RpdGxl\nIiB2YWx1ZT0idHJ1ZSIgLz4KPC93aWRnZXQ+\n'.decode(
            "base64")
        home = self.zwalk.read(tmplocation + "assets/www/index.html")
        if not nonxwalk:
            home = home.replace(
                'Apache Cordova</h1>', 'Apache Cordova (with Crosswalk)</h1>')
        css = self.zwalk.read(tmplocation + "assets/www/css/index.css")
        jees = self.zwalk.read(tmplocation + "assets/www/js/index.js")
        logos = self.zwalk.read(tmplocation + "assets/www/img/logo.png")
        if screen.lower() == "fullscreen":
            manifest = manifest.replace(
                "Theme.Black.NoTitleBar", "Theme.NoTitleBar.Fullscreen")
            config = config.replace(
                'value="DEBUG" />', 'value="DEBUG" />\n\t<preference name="fullscreen" value="true" />')
        if orientation.lower() == "landscape":
            manifest = manifest.replace(
                'activity_name"', 'activity_name"\n                android:screenOrientation="landscape"')
            config = config.replace(
                'value="DEBUG" />', 'value="DEBUG" />\n\t<preference name="orientation" value="landscape" />')
        try:
            cordovajs = self.zwalk.read(
                tmplocation + "assets/www/cordova.js")
        except:
            cordovajs = self.zwalk.read(
                self.nl[0] + "framework/assets/www/cordova.js")
        screens = ["-hdpi", "-ldpi", "-mdpi", "-xhdpi", ""]
        dirsx = ["src/%s" % uid.replace(".", "/"), "res/values", "res/xml", "assets/www",
                 "assets/www/img", "assets/www/css", "assets/www/js"] + ["res/drawable" + i for i in screens]
        for i in dirsx:
            makedirs(path.join(proj, i))
        for i in screens:
            open(path.join(path.join(proj, "res"), path.join(
                "drawable" + i), "icon.png"), "w").write(iconraw)
        open(path.join(proj, "AndroidManifest.xml"), "w").write(manifest)
        open(path.join(proj, "src/%s/MainActivity.java" %
                       uid.replace(".", "/")), "w").write(activity)
        open(path.join(proj, "res/values/strings.xml"), "w").write(strings)
        open(path.join(proj, "res/xml/config.xml"), "w").write(config)
        open(path.join(proj, "assets/www/cordova.js"), "w").write(cordovajs)
        open(path.join(proj, "assets/www/index.html"), "w").write(home)
        open(path.join(proj, "assets/www/js/index.js"), "w").write(jees)
        open(path.join(proj, "assets/www/css/index.css"), "w").write(css)
        open(path.join(proj, "assets/www/img/logo.png"), "w").write(logos)
        Extract(self.nl[0] + "framework/", proj, xmls=self.zwalk)
        open(path.join(proj, "project.properties"), "w").write(
            "android.library.reference.1=framework")
        try:
            shutil.rmtree(path.join(proj, "framework", "res"))
            shutil.rmtree(path.join(proj, "framework", "assets"))
            shutil.rmtree(path.join(proj, "framework", "test"))
        except:
            pass

xwalkr = [0, 0]
nonxwalk = [True]


def verifyid(parser, x):
    if not re.match("^[a-z][a-z0-9]*\.[a-z0-9\.]*$", x):
        parser.error("Package ID tidak valid")
    return x


def isvalidzip(parser, x):
    fn = path.join(pwd, x)
    if path.exists(fn):
        if not is_zipfile(fn):
            parser.error("'%s' bukan zip file" % x)
        else:
            zp = ZipFile(fn)
            nl = zp.namelist()
            xdet = re.findall("^crosswalk-cordova-([\w\.-]*)-(\w*)/$", nl[0])
            if not xdet:
                if not re.match("^cordova-android-(.*?)/$", nl[0]):
                    parser.error("'%s' bukan crosswalk cordova bundle" % x)
                else:
                    xwalkr[0] = "?"
                    xwalkr[1] = "?"
                    nonxwalk[0] = True
            else:
                xwalkr[0] = xdet[0][0]
                xwalkr[1] = xdet[0][1]
                nonxwalk[0] = False
    else:
        parser.error("'%s' tidak ditemukan" % x)
    return x


def isavailable(parser, x):
    if not re.match("^[a-zA-Z0-9-_\. ]*$", x):
        parser.error("Nama tidak valid")
    fn = path.join(pwd, x)
    if path.exists(fn):
        parser.error("'%s' sudah ada, ganti nama lain" % x)
    return x
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Crosswalk Cordova Builder by Agus Ibrahim. it's recomended for programmers who developing Android Cordova using AIDE.")
    parser.add_argument(
        'bundle', type=lambda x: isvalidzip(parser, x), help="Crosswalk zip bundle")
    parser.add_argument(
        'uid', type=lambda x: verifyid(parser, x), help="Package id")
    parser.add_argument(
        'name', type=lambda x: isavailable(parser, x), help="Project name")
    parser.add_argument(
        '--fullscreen', action="store_true", help="set Fullscreen")
    parser.add_argument(
        '--landscape', action="store_true", help="set Landscape")
    args = parser.parse_args()
    bunlde = args.bundle
    uid = args.uid
    name = args.name
    landscape = {True: "landscape", False: "potrait"}[args.landscape]
    fullscreen = {True: "fullscreen", False: "normal"}[args.fullscreen]
    lines = "=" * 30
    print "Crosswalk Cordova Generator\n%s\nID: %s\nName: %s\nCrosswalk version: %s\nCPU: %s" % (lines, uid, name, xwalkr[0], xwalkr[1])
    print lines
    try:
        i = raw_input("Continue? (Y/n)")
    except:
        i = None
    if i.lower() in ["y", "yes", "ya"]:
        print "Please wait..."
        xx = XWalkbuilder(path.join(pwd, bunlde))
        xx.make(uid, name, fullscreen, landscape, nonxwalk=nonxwalk)
        print "Done\n" + path.join(pwd, name)
    else:
        print "Canceled"
