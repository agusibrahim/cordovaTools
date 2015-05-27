import xml.etree.cElementTree as ET
from os import makedirs, path, remove, listdir, getcwd, rmdir, popen3
from zipfile import ZipFile, is_zipfile
from urllib import urlopen, urlretrieve
import re
import traceback
import json
import sys
from subprocess import Popen, PIPE
"""
ET.register_namespace("", "http://apache.org/cordova/ns/plugins/1.0")
ET.register_namespace("m3", "http://m3.org/cordova/ns/plugins/1.0")
ET.register_namespace("rim", "http://rim.org/cordova/ns/plugins/1.0")
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
"""
platformList = ["browser", "firefoxos", "android", "amazon-fireos",
                "ubuntu", "ios", "blackberry10", "wp7", "wp7", "windows", "windows8"]
pwd = getcwd()


def xmlify(s):
  s = re.sub('xmlns.*"', '', s)
  s = s.replace("android:", "__xxx__")
  s = re.sub("<ns\d:", "<", s)
  s = re.sub("</ns\d:", "</", s)
  s = re.sub("<(\w*?):(\w*?) ", r"<\1--\2 ", s)
  s = re.sub("<(\w*?):(\w*?)", r"<\1--\2", s)
  s = re.sub("</(\w*?):(\w*?)", r"</\1--\2", s)
  # print s
  return s


def xfind(xml, path):
  tag, attr = path.split("@")
  k, v = attr.split("=")
  tag = tag
  return [i for i in xml.findall(tag) if i.attrib[k] == v]


def rmcomment(ss):
  return "\n".join([i for i in ss.splitlines() if not i.strip().startswith("//")])


def xmlindent(s):
  from xml.dom import minidom
  s = s.encode("utf-8")
  xmlheader = re.compile(b"<\?.*\?>").match(s)
  s = re.compile(b'>\s+([^\s])', re.DOTALL).sub(b'>\g<1>', s)
  s = s.replace(b'<![CDATA[', b'%CDATAESTART%').replace(b']]>', b'%CDATAEEND%')
  try:
    s = minidom.parseString(s).toprettyxml()
  except Exception as e:
    pass
  s = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL).sub('>\g<1></', s)
  s = s.replace('%CDATAESTART%', '<![CDATA[').replace('%CDATAEEND%', ']]>')
  s = s.replace("<?xml version=\"1.0\" ?>", "").strip()
  if xmlheader:
    s = xmlheader.group().decode("utf-8") + "\n" + s
  if not s.startswith("<?xml "):
    s = "<?xml version='1.0' encoding='utf-8'?>\n" + s
  if s.count("__xxx__versionCode"):
    s = s.replace("__xxx__", "android:")
  s = s.replace("&gt;", ">").replace("&lt;", "<")
  return s


def jsonindent(s, indent=4):
  s = json.dumps(s).replace('"clobbers":', '"zclobbers":')
  parsed = json.loads(s)
  res = json.dumps(
      parsed, sort_keys=True, indent=indent, separators=(',', ': '))
  res = res.replace('"zclobbers":', '"clobbers":')
  return res


class plugReg:

  def __init__(self, pwd, ids):
    self.pwd = pwd
    self.ids = ids
    try:
      self.data = json.load(open(path.join(self.pwd, ".plugreg")))
    except IOError:
      self.data = {}
    if not self.ids in self.data:
      self.data[self.ids] = {"files": [], "nodes": {}}

  def shrink(self, pat):
    if pat.startswith(self.pwd + "\\"):
      return pat[len(self.pwd + "\\"):]
    else:
      return pat

  def add(self, f):
    if not f in self.data[self.ids]["files"]:
      self.data[self.ids]["files"].append(self.shrink(f))

  def addNode(self, f, node):
    self.data[self.ids]["nodes"][f] = node

  def commit(self):
    open(path.join(self.pwd, ".plugreg"), "w").write(
        jsonindent(self.data, indent=2))


class corPlugs:

  def __init__(self, ss=None):
    if not ss:
      ss = "cordova.define('cordova/plugin_list', function(require, exports, module) {\nmodule.exports = [\n]});"
    else:
      ss = rmcomment(ss)
    self.exports = json.loads(re.split("module.exports.metadata ?= ?", re.split(
        "module.exports ?= ?", ss)[1])[0].replace("});", "").replace(";", ""))
    if re.search("module.exports.metadata ?= ?", ss):
      self.metadata = json.loads(
          re.split("module.exports.metadata ?= ?", ss)[1].replace(";", ""))
    else:
      self.metadata = {}

  def getInstalled(self):
    return self.metadata

  def getExports(self):
    return self.exports

  def addMetadata(self, id, ver="1.0"):
    self.metadata[id] = ver
    return self.metadata

  def setExports(self, exi):
    self.exports.append(exi)
    return self.exports

  def addPlugin(self, jm, id, ver, zipo, proj, root, regi):
    src = jm.attrib["src"]
    cn = path.basename(path.splitext(src)[0])
    plug = {}
    ff = "plugins/" + id + "/" + src

    ######## JS-MODULE WRITER #######
    if sys.platform == "win32":
      ffw = ff.replace("/", "\\")
    else:
      ffw = ff
    rsrc = path.join(root, src)
    raw_src = zipo.read(rsrc)
    target = path.join(proj, "assets", "www", ffw)
    target_dir = path.dirname(target)
    if not path.exists(target_dir):
      makedirs(target_dir)
    inc = 'cordova.define("%s", function(require, exports, module) { \n' % (
        id + "." + path.splitext(path.basename(target))[0])
    open(target, "w").write(inc + raw_src + "\n\n});")
    regi.add(target)
    #################################

    plug["file"] = ff
    if "/".join(path.dirname(ff).split("/")[-2:]) in ["www/" + i for i in platformList]:
      cn = cn + "_" + path.dirname(ff).split("/")[-1:][0]
    plug["id"] = id + "." + cn
    for com in jm.getchildren():
      if "target" in com.attrib:
        if com.tag in plug:
          plug[com.tag].append(com.attrib["target"])
        else:
          plug[com.tag] = [com.attrib["target"]]
    # if not id in self.metadata.keys():
    # print id+"."+path.splitext(src)[0] ;print   [i["id"] for i in
    # self.exports]
    if not id + "." + path.splitext(path.basename(src))[0] in [i["id"] for i in self.exports]:
      self.exports.append(plug)
      self.metadata[id] = ver

  def rmPlugin(self, id):
    rems = [h for h in self.exports if h["id"].startswith(id)]
    for rem in rems:
      idx = self.exports.index(rem)
      del self.exports[idx]
    if id in self.metadata:
      del self.metadata[id]
    return self.exports

  def commit(self, out=False):
    gg = "cordova.define('cordova/plugin_list', function(require, exports, module) {\nmodule.exports = %s});\n\nmodule.exports.metadata = %s" % (
        jsonindent(self.exports), jsonindent(self.metadata))
    if out:
      open(out, "w").write(gg)
    return gg
def sendcmd(cmd):
    p=Popen(cmd.split(), stdout=PIPE)
    return p.communicate()[0]

class virtualzip:

  def __init__(self, dir):
    self.dir = dir

  def fixname(self, n, dn):
    isdir = path.isdir(path.normpath(n.replace('\n', '')))
    n = n.replace('\n', '').replace('\\', '/').replace("//", "/")
    if dn:
      n = n[len(dn) + 1:]
    if isdir and not n.endswith("/"):
      n = n + "/"
    return n

  def namelist(self):
    ss= map(lambda x: self.fixname(x, path.dirname(self.dir)), sendcmd("find " + self.dir).splitlines())
    return ss

  def read(self, fn):
    return open(path.normpath(path.join(path.dirname(self.dir), fn))).read()


class PluginParse:

  def install(self, ZipPlugin, project, platform, isdepend=0):
      # install plugin
    if path.exists(path.join(ZipPlugin, "plugin.xml")):
      self.zipo = virtualzip(ZipPlugin)
    else:
      self.zipo = ZipFile(ZipPlugin)
    self.namelist = self.zipo.namelist()
    self.project = project
    if "plugin.xml" in self.namelist:
      self.root = ""
    else:
      self.root = self.namelist[0]
    self.xml = ET.fromstring(xmlify(self.zipo.read(self.root + "plugin.xml")))
    self.platform = xfind(self.xml, "platform@name=" + platform)[0]
    self.uidp = self.xml.attrib["id"]
    self.vers = self.xml.attrib["version"]
    self.isdepend = isdepend
    self.regi = plugReg(self.project, self.uidp)
    if not self.isdepend:
      if not self.isInstalled(self.uidp, self.vers):
        if verbose:
          print "'isInstalled' aborted the process"
        return
    if not self.isdepend:
      print "Installing " + self.uidp
      if not self.show_info():
        if verbose:
          print "user canceled"
        return
    else:
      print "    Install " + self.uidp
    var = self.variable()
    if type(var) == dict:
      for k, v in var.items():
        self.xml = ET.fromstring(ET.tostring(self.xml).replace("$" + k, v))
        self.platform = xfind(self.xml, "platform@name=" + platform)[0]
    else:
      if verbose:
        print "batal"
      return
    if verbose:
      print "running JS Module handler"
    self.jsmodule_handler()
    if verbose:
      print "running Copy file"
    self.sourceFile_handler()
    if verbose:
      print "running Copy assets"
    self.assets_handler()
    if verbose:
      print "running Config handler"
    self.config_handler()
    if verbose:
      print "running Framework handler"
    self.framework_handler()
    if verbose:
      print "running Dependency handler"
    self.depend()
    if verbose:
      print "Updating registry..."
    self.regi.commit()
    return self.uidp
    # print "ok"

  def uninstall(self, uid):
    coc = corPlugs(
        open(path.join(pwd, "assets", "www", "cordova_plugins.js")).read())
    if not uid in coc.getInstalled():
      print "%s not Installed" % uid
      return
    pr = plugReg(pwd, uid)
    if uid in pr.data:
      if verbose:
        print "deleting files..."
      self.rmfiles(pr.data[uid]["files"])
      if verbose:
        print "deleting nodes..."
      self.rmNodes(pr.data[uid]["nodes"])
    if verbose:
      print "removing from cordova_plugins.js..."
    coc.rmPlugin(uid)
    coc.commit(out=path.join(pwd, "assets", "www", "cordova_plugins.js"))
    if verbose:
      print "removing from plugin registry..."
    reg = plugReg(pwd, uid)
    del reg.data[uid]
    reg.commit()
    if verbose:
      print "Done"

  def rmNodes(self, nodes):
    for target, node in nodes.items():
      target, parent = target.split("::")
      childs = ET.fromstring(node).getchildren()
      if sys.platform == "win32":
        target = target.replace("/", "\\")
      xconfig = ET.fromstring(xmlify(open(path.join(pwd, target)).read()))
      if parent.startswith("/"):
        config = ET.Element("roots")
        config.append(xconfig)
        parent = parent[1:]
      else:
        config = xconfig
      root = config.findall(parent)
      if root:
        root = root[0]
      else:
        cfg = config.tag == "roots"
        if cfg:
          root = config.getchildren()[0]
        else:
          root = config
        #raw_input("ORA NEMU "+self.uidp)
      for cil in childs:
        root  # uses-permission
        if cil.tag == "uses-permissions":
          print "we keep uses-permission tag, if you don't want please delete manualy"
        else:
          # print cil.attrib
          atrib = [{str(i.attrib): i} for i in root.getchildren()]
          idx = [v.values()[0] for v in atrib if str(cil.attrib) in v]
          # print idx
          if idx:
            root.remove(idx[0])

            # root.remove(ada[0])
      if config.tag.strip().endswith("roots"):
        if config.getchildren()[0].tag == "manifest":
          config.find("manifest").set(
              "xmlns:android", "http://schemas.android.com/apk/res/android")
        open(path.join(pwd, target), "w").write(
            xmlindent(ET.tostring(config.getchildren()[0])))
      else:
        if config.tag == "manifest":
          config.set(
              "xmlns:android", "http://schemas.android.com/apk/res/android")
        open(path.join(pwd, target), "w").write(xmlindent(ET.tostring(config)))

  def rmfiles(self, files):
    ada = 0
    for h in files:
      hk = path.join(pwd, h)
      dn = path.dirname(hk)
      try:
        remove(hk)
        ada = 1
      except OSError:
        break
      while ada:
        if not len(listdir(dn)):
          rmdir(dn)
          dn = path.dirname(dn)
        else:
          break

  def isInstalled(self, id, ver):
    coc = corPlugs(
        open(path.join(self.project, "assets", "www", "cordova_plugins.js")).read())
    pack = coc.getInstalled()
    if id in pack:
      if pack[id] != ver:
        msg = "%s Already installid with ver %s. Update plugin?(y/N) "
      else:
        msg = "%s:%s Already installid. reinstall it?(y/N) "
      try:
        i = raw_input(msg % (id, pack[id]))
        if i.lower() in ['ya', 'y', 'yay', 'yes']:
          return True
        else:
          return
      except:
        return
    else:
      return True

  def findid(self, proj):
    # find package/plugin id from all zip in current directory
    ids = {}
    for i in listdir(proj):
      if not i.endswith(".zip"):
        continue
      else:
        if not is_zipfile(path.join(proj, i)):
          continue
      zix = ZipFile(path.join(proj, i))
      namelist = zix.namelist()
      if "plugin.xml" in namelist:
        root = ""
      else:
        root = namelist[0]
      if not root + "plugin.xml" in namelist:
        del namelist, zix
        continue
      try:
        xml = ET.fromstring(xmlify(zix.read(root + "plugin.xml")))
        ids[xml.attrib["id"]] = i
        del namelist, zix
      except:
        pass
    return ids

  def depend(self):
    # <dependency handler
    ids = []
    for i in self.xml.findall("dependency"):
      if not ids:
        ids = self.findid(self.project)
      id = i.attrib["id"]
      print "Dependency with %s \n    Searching..." % id
      if id in ids:
        print "    Found " + ids[id]
        self.install(
            path.join(self.project, ids[id]), self.project, self.platform.attrib["name"], 1)
      else:
        print "    Dependency not Found. WARNING: Plugin may not work"

  def variable(self):
    # variable setup handler

    ada = 0
    vari = {}
    for target in (self.xml, self.platform):
      # print target.getchildren()
      for i in target.findall("preference"):
        attr = i.attrib
        try:
          if ada == 0:
            print "======= VARIABLE SETUP ========"
          ada = 1
          var = raw_input(attr.values()[0] + ": ")
          if not var:
            return None
          vari[attr.values()[0]] = var
        except:
          return None
    return vari

  def show_info(self):
    # <info handler
    for target in (self.xml, self.platform):
      for i in target.findall("info"):
        print i.text
    try:
      cc = raw_input("Continue install %s? (y/N)" % self.uidp)
      if cc.lower() in ['y', 'ya', 'yes', 'yay']:
        return True
      else:
        return None
    except:
      return None

  def jsmodule_handler(self):
    # js-module and cordova_plugins.js handler
    tt = path.join(pwd, "assets", "www", "cordova_plugins.js")
    if path.exists(tt):
      arg = open(tt).read()
    else:
      arg = None
    cc = corPlugs(arg)
    for target in (self.xml, self.platform):
      for i in target.findall("js-module"):
        cc.addPlugin(
            i, self.uidp, self.vers, self.zipo, self.project, self.root, self.regi)
    cc.commit(out=tt)

  def extract(self, src, target, regi=None, onself=0, xmls=None):
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
            if regi:
              regi.add(path.join(target_fix, fn))
          else:
            if onself:
              open(target, "w").write(raw_src)
              if regi:
                regi.add(target)
            else:
              if not path.exists(target_fix):
                makedirs(target_fix)
              open(path.join(target_fix, fn), "w").write(raw_src)
              if regi:
                regi.add(path.join(target_fix, fn))

  def sourceFile_handler(self):
    for target in (self.xml, self.platform):
      for i in target.findall("source-file"):
        src = i.attrib["src"]
        target_dir = i.attrib["target-dir"]
        src = path.join(self.root, src)
        if sys.platform == "win32":
          target_dir = target_dir.replace("/", "\\")
        target_in_project = path.join(self.project, target_dir)
        self.extract(src, target_in_project, self.regi)

  def assets_handler(self):
    for target in (self.xml, self.platform):
      for i in target.findall("asset"):
        src = path.join(self.root, i.attrib["src"])
        target = path.join(self.project, "assets", "www", i.attrib["target"])
        if sys.platform == "win32":
          target = target.replace("/", "\\")
        if target.endswith("\\"):
          target = target[:-1]
        self.extract(src, target, self.regi, 1)

  def config_handler(self):
    for target in (self.xml, self.platform):
      for i in target.findall("config-file"):
        target = i.attrib["target"]
        parent = i.attrib["parent"]
        childs = i.getchildren()
        self.regi.addNode(target + "::" + parent, ET.tostring(i))
        if sys.platform == "win32":
          target = target.replace("/", "\\")
        xconfig = ET.fromstring(
            xmlify(open(path.join(self.project, target)).read()))
        if parent.startswith("/"):
          config = ET.Element("roots")
          config.append(xconfig)
          parent = parent[1:]
        else:
          config = xconfig
        root = config.findall(parent)
        if root:
          root = root[0]
        else:
          cfg = config.tag == "roots"
          if cfg:
            root = config.getchildren()[0]
          else:
            root = config
          #raw_input("ORA NEMU " + self.uidp)
          if verbose:
            print "Fatal error, skip (my not work)"
        for cil in childs:
          pos = [i.tag for i in root.getchildren()]
          if cil.tag in pos:
            pos = len(
                pos) - (x for x in (y for y in enumerate(pos[::-1]))if x[1] == cil.tag).next()[0] - 1
          else:
            pos = -1
          # metode autentikasi yang rumit #_#
          if not cil.attrib:
            if not [i.attrib for i in cil.getchildren()] in [[x.attrib for x in i.getchildren()] for i in root.getchildren()]:
              if pos == -1:
                root.append(cil)
              else:
                root.insert(pos + 1, cil)
            else:
              if verbose:
                print "Already exists, skip>>"
          else:
            if not cil.attrib in [i.attrib for i in root.getchildren()]:
              if pos == -1:
                root.append(cil)
              else:
                root.insert(pos + 1, cil)
            else:
              if verbose:
                print "Already exist, skip>>", cil.tag
        if config.tag.strip().endswith("roots"):
          if config.getchildren()[0].tag == "manifest":
            config.find("manifest").set(
                "xmlns:android", "http://schemas.android.com/apk/res/android")
          open(path.join(self.project, target), "w").write(
              xmlindent(ET.tostring(config.getchildren()[0])))
        else:
          if config.tag == "manifest":
            config.set(
                "xmlns:android", "http://schemas.android.com/apk/res/android")
          open(path.join(self.project, target), "w").write(
              xmlindent(ET.tostring(config)))

  def framework_handler(self):
    for target in (self.xml, self.platform):
      for i in target.findall("framework"):
        src = i.attrib["src"]
        if verbose:
          print "Installing framework %s" % src
        custom = i.attrib["custom"]  # unused i dont understand for what
        ########### extract framework #################
        sumur = path.join(self.root, src)
        if sumur + "/" in self.namelist:
          sumur = sumur + "/"
        self.extract(sumur, self.project, self.regi)
        ########## project.properties handler #########
        clib = path.join(self.project, "project.properties")
        try:
          liv = open(clib).read()
          numl = [int(i) for i in re.findall(
              "android\.library\.reference\.(\d*?) ?=", liv)]
          if numl:
            ke = max(numl) + 1
            if not re.search("\.\d ?= ?%s$" % path.basename(src), liv):
              open(clib, "w").write("%s\nandroid.library.reference.%s=%s" %
                                    (liv, ke, path.basename(src)))
          else:
            open(clib, "w").write("%s\nandroid.library.reference.1=%s" %
                                  (liv, path.basename(src)))
        except IOError:
          open(clib, "w").write(
              "android.library.reference.1=" + path.basename(src))


class makeProject:

  def __init__(self):
    self.repourl = "http://127.0.0.1:8000/repo.json"

  def init(self, ver=None):
    try:
      repodata = json.load(urlopen(self.repourl))
    except:
      print "Could't fetch cordova repository"
      return
    latest = [x for x in repodata if x["name"] == max(
        [(re.sub("\D", "", i["name"]), i["name"]) for i in repodata])[1]]
    if ver:
      ss = [i for i in repodata if i["name"] == ver]
      if ss:
        selected = ss[0]
      else:
        print "Cordova %s not found. Available: %s" % (ver, ", ".join([i["name"] for i in repodata]))
        return
    else:
      selected = latest
    self.download(selected["zipball_url"])

  def download(self, url):
    cordovaball = path.join(pwd, "_cordovalib")
    try:
      urlretrieve(url, cordovaball)
    except:
      print "Download error"
      return
    self.make(cordovaball)

  def make(self, cball):
    zball = ZipFile(cball)
    root = zball.namelist()[0]
    p = PluginParse()
    p.extract(root + "framework/", "mama", onself=1, xmls=zball)
    del zball


def plugmaker(pid, name, jstmp, javatmp):
  pl = ET.Element("plugin")
  pl.set("id", pid)
  pl.set("version", "1.0")
  pl.set("xmlns", "http://apache.org/cordova/ns/plugins/1.0")
  pl.set("xmlns:android", "http://schemas.android.com/apk/res/android")
  pl.append(ET.fromstring(
      "<engines><engine name='cordova' version=\">=3.0.0\"/></engines>"))
  pl.append(ET.fromstring("<name>%s</name>" % name))
  pl.append(
      ET.fromstring("<description>%s my awesome plugin</description>" % name))
  pl.append(ET.fromstring("<author>Agus Ibrahim</author>"))
  jsm = ET.Element("js-module")
  jsm.set("src", "www/%s.js" % name)
  jsm.set("name", name)
  jsm.append(ET.fromstring("<clobbers target=\"%s\" />" % name))
  pl.append(jsm)
  plat = ET.Element("platform", {"name": "android"})
  plat.append(ET.fromstring(
      '<config-file target="res/xml/config.xml" parent="/*"><feature name="%s" ><param name="android-package" value="%s.%s"/></feature></config-file>' % (name, pid, name)))
  plat.append(ET.fromstring(
      '<source-file src="src/android/%s.java" target-dir="src/%s" />' % (name, pid.replace(".", "/"))))
  pl.append(plat)
  pd = path.join(pwd, name)
  makedirs(pd)
  makedirs(path.join(pd, "www"))
  makedirs(path.join(pd, "src", "android"))
  open(path.join(pd, "www", name + ".js"), "w").write(jstmp)
  open(path.join(pd, "src", "android", name + ".java"), "w").write(javatmp)
  open(path.join(pd, "plugin.xml"), "w").write(xmlindent(ET.tostring(pl)))


import argparse
parser = None
mode = None
verbose = False


class readable_dir(argparse.Action):

  def __call__(self, parser, namespace, values, option_string=None):
    prospective_dir = values
    if mode in ["install", "installdebug", "remove", "list"]:
      cd = getcwd()
      if not len([i for i in [path.join(cd, "AndroidManifest.xml"), path.join(cd, "res", "xml", "config.xml"), path.join(cd, "assets", "www", "index.html")] if path.exists(i)]) == 3:
        parser.error("Please CD into cordova project directory")
    if mode != "list":
      if values == "null":
        parser.error("too few arguments")
    try:
      coc = corPlugs(
          open(path.join(pwd, "assets", "www", "cordova_plugins.js")).read())
    except:
      coc = {}
    p = PluginParse()
    if mode in ["install", "installdebug"]:
      if mode == "installdebug":
        setverbose(True)
      if re.match("^.*github.com/.+/.+\.git", values):
        print "Downloading plugin..."
        try:
          urlretrieve(
              values.replace(".git", "/archive/master.zip"), ".plugintoinstall.zip")
          if verbose:
            print "Download OK"
          prospective_dir = ".plugintoinstall.zip"
          values = ".plugintoinstall.zip"
        except:
          parser.error("Download failed")
      if not path.exists(prospective_dir):
        parser.error("'%s' not exists" % prospective_dir)
      else:
        if is_zipfile(prospective_dir):
          try:
            res = p.install(values, pwd, "android")
            if res:
              print res + " successfully installed!"
            setattr(namespace, self.dest, prospective_dir)
          except:
            parser.error("Install failed:\n" + traceback.format_exc())
        elif path.exists(path.join(prospective_dir, "plugin.xml")):
          try:
            res = p.install(values, pwd, "android")
            if res:
              print res + " successfully installed!"
            setattr(namespace, self.dest, prospective_dir)
          except:
            parser.error("Install failed:\n" + traceback.format_exc())
        else:
          parser.error("Not zip file or plugin.xml not found")
    elif mode == "create":
      if re.match("[a-z][a-z0-9]*\.[a-z0-9\.]*", prospective_dir.lower()):
        setattr(namespace, self.dest, prospective_dir)
      else:
        parser.error("Invalid plugin ID")
    elif mode == "list":
      for k in coc.getInstalled().items():
        print "%s: %s" % k
      setattr(namespace, self.dest, prospective_dir)
    elif mode == "remove":
      if not values in coc.getInstalled():
        parser.error("%s not Installed" % values)
      else:
        try:
          jwb = raw_input("Remove '%s'? (Y/n)" % values)
          if jwb != "Y":
            setattr(namespace, self.dest, prospective_dir)
            return
        except:
          setattr(namespace, self.dest, prospective_dir)
          return
        try:
          p.uninstall(values)
          print values + " has been removed!"
          setattr(namespace, self.dest, prospective_dir)
        except:
          parser.error("Remove failed:\n" + traceback.format_exc())


def checkname(x, parser):
  if mode != "create":
    return
  if re.match("^[a-z][a-z0-9]*$", x.lower()):
    if path.exists(path.join(pwd, x)):
      parser.error("'%s' already exists" % x)
    else:
      return x
  else:
    parser.error("Invalid name")


def setmode(x):
  global mode
  mode = x
  return x


def setverbose(x):
  global verbose
  verbose = x
parser = argparse.ArgumentParser(
    description="PLUGME - Cordova plugin manager.\nCrafted by Agus Ibrahim\n(@agusmibrahim)", usage="plugme (install|installdebug|remove|create|list) [PATH/id]")
parser.add_argument(
    "mode", choices=["install", "installdebug", "remove", "create", "list"], type=lambda x: setmode(x))
parser.add_argument(
    "path", metavar="PATH/PluginID", default="null", nargs="?", action=readable_dir, help="Plugin file/folder or Plugin ID")
parser.add_argument(
    "-name", type=lambda x: checkname(x, parser), help="name for created plugin", default="myPlugin")
parser.add_argument(
    "-m", action="append", metavar="pluginMethod", default=None, help="Plugin method")
parser.add_argument(
    "-i", metavar="indentSize", default=4, help="Plugin indent size")
#parser.add_argument("--verbose", action='store_true', default=False, help="print process")
arr = parser.parse_args()
if arr.mode == "create":
  name = arr.name or "myPlugin"
  method = arr.m or ["say"]
  jst = "function %s(){}\n" % name
  jvt = "package %s;\n\nimport org.apache.cordova.CallbackContext;\nimport org.apache.cordova.CordovaPlugin;\nimport org.json.JSONArray;\nimport org.json.JSONException;\n\npublic class %s extends CordovaPlugin {\n\t@Override\n\tpublic boolean execute(String action, JSONArray args, CallbackContext callbackContext) throws JSONException {" % (
      arr.path, name)
  for i in method:
    jst += "\n%s.prototype.%s=function(data, callbackOK, callbackErr){\n\tcordova.exec(callbackOK, callbackErr, '%s', '%s', [data]);\n}" % (
        name, i, name, i)
    if jvt.endswith("\t}"):
      cond = "else if"
    else:
      cond = "\n\t\tif"
    jvt += "%s (action.equals(\"%s\")) {\n\t\t\tString data = args.getString(0);\n\t\t\tcallbackContext.success(\"%s: \"+data);\n\t\t}" % (
        cond, i, i)
  jst += "\nmodule.exports=new %s();" % name
  jvt += "else{\n\t\t\treturn false;\n\t\t}\n\t\treturn false;\n\t}\n}"
  indent = " " * arr.i
  jvt = jvt.replace('\t', indent)
  jst = jst.replace('\t', indent)
  plugmaker(arr.path, name, jst, jvt)
