import traceback
import sys, os
import datetime
import shutil
import glob
from os.path import abspath, dirname
from os.path import join as pj, splitext, exists, split
from path import path
from collections import OrderedDict

from openalea.release.utils import make_silent, Later, url, unpack, \
into_subdir, in_dir, try_except, TemplateStr, sh, sj, makedirs, \
Pattern, recursive_glob_as_dict, get_logger
                                
logger = get_logger()

############################################
# Formula                                  #
############################################
class Formula(object):
    required_tools = None
    version = '1.0'
    description = ""
    homepage = ""
    licence = ""
    authors = ""
    # The URL to fetch the sources from
    # A None url implies the download has already done by someone else
    download_url = None
    # Name of the  local archive
    download_name  = ""
    #OrderedDict mapping of
    # task id and (the name of the method to call, task can be skipped boolean)
    # Task management:
    all_tasks       = OrderedDict([ ("d",("download",True)),
                                    ("a",("unpack",True)),
                                    ("p",("patch", True)),
                                    ("c",("configure",True)),
                                    ("m",("make",True)),
                                    ("i",("install",True)),
                                    ("b",("bdist_egg",True)),
                                    ("u",("upload_egg",True)),
                                    ("g",("copy_egg",True)),
                                    
                                    ("x",("extend_sys_path",False)),
                                    ("y",("extend_python_path",False)),
                                    ])
    #string of task ids that this particular builder supports (eg. "duf")
    # Only execute these tasks:
    supported_tasks = "".join(all_tasks.keys())
    #string of tasks for which stdout can be decently swallowed
    # swallow stdout for these tasks:
    silent_tasks    = "fxy"
    # The egg depends on the Python version (allows correct egg naming)
    py_dependent   = True
    # The egg depends on the os and processor type (allows correct egg naming)
    arch_dependent = True 
    
    archive_subdir = None
    
    # If you put it on True, this means that you have the     
    # corresponding library installed. This is because they    
    # are too difficult to compile and that we don't actually  
    # need to compile them (no linkage from us to them)        
    # or that they come as .exes and not eggs already  
    yet_installed = False
    
    __packagename__ = None
    
    working_path  = os.getcwd()

    def __init__(self,**kwargs):
        self.done_tasks = {}
        self.options = {} 
        self.pending = None
        self.archname  = pj( self._get_dl_path() , self.download_name)
        self.sourcedir = pj( self._get_src_path(), splitext(self.download_name)[0] )
        self.installdir = pj( self._get_install_path(), splitext(self.download_name)[0] )
        self.install_inc_dir = pj(self.installdir, "include")
        self.install_lib_dir = pj(self.installdir, "lib")        
        
        
        # Variable to check if the source directory is yet fixed
        self._source_dir_fixed = False

        if "no_env" in kwargs:
            self.eggdir         = ""
            self.setup_in_name  = ""
        else:
            self.eggdir         = pj(self._get_egg_path(), self.egg_name())
            self.setup_in_name  = pj(abspath(dirname(__file__)), "setup.py.in")
        self.setup_out_name = pj(self.eggdir, "setup.py")
        self.use_cfg_login  = False
        
        makedirs(self._get_src_path())
        makedirs(self._get_install_path())
        makedirs(self._get_dl_path())
        makedirs(self.eggdir)
        

        self.default_substitutions = dict( NAME             = self.egg_name(),
                                       VERSION              = self.version,
                                       THIS_YEAR            = datetime.date.today().year,
                                       SETUP_AUTHORS        = "Openalea Team",
                                       CODE_AUTHOR          = self.authors,
                                       DESCRIPTION          = self.description,
                                       HOMEPAGE             = self.homepage,
                                       URL                  = self.download_url,
                                       LICENSE              = self.licence,

                                       ZIP_SAFE             = False,
                                       PYTHON_MODS          = None,
                                       PACKAGES             = None,
                                       PACKAGE_DIRS         = None,
                                       PACKAGE_DATA         = {},
                                       DATA_FILES           = None,

                                       INSTALL_REQUIRES     = self.required_tools,
                                       
                                       LIB_DIRS         = {'lib' : pj(self.sourcedir,'lib') },
                                       INC_DIRS         = {'include' : pj(self.sourcedir,'include') },
                                       BIN_DIRS         = {'bin' : pj(self.sourcedir,'bin') },
                                       )
        
        if self.yet_installed:
            try:
                self.package
            except Exception:
                self.enabled = False
            else:
                self.enabled = True
        
    @property
    def name(self):
        return self.__class__.__name__

    @property
    def has_pending(self):
        if self.pending is None:
            self.__find_pending_tasks()
        return len(self.pending) != 0

    def get_task_restriction_projs(self):
        return self.options.get("only_action_projs")
        
    def __find_pending_tasks(self):
        tasks = []
        name  = self.name
        for task in self.supported_tasks:
            task_func, skippable = self.all_tasks.get('_'+task, (None, None))
            if task_func == skippable == None:
            # This happens with the --no-upload option
            # that removes tasks from all_tasks
                continue
            done   = self.is_task_done(name, task)
            forced = False
            restriction = self.get_task_restriction_projs()
            if restriction != None:
                forced = task in restriction
            else:
                forced = self.is_task_forced(name, task)
            skip = done and not forced and skippable
            if not skip:
                tasks.append((task, task_func, skippable))
        self.pending = tasks

    def __has_pending_verbose_tasks(self):
        for task, func, skippable in self.pending:
            if task not in self.silent_tasks:
                return True
        return False
        
    @classmethod
    def egg_name(cls):
        return cls.__name__.strip("egg_")

    def get_task_restriction_eggs(self):
        return self.options.get("only_action_eggs")

    def process_me(self, only):
        should_process = only is None or self.name in only
        make_silent( not self.__has_pending_verbose_tasks() or \
                              not should_process )

        # forced_tasks is a string containing self.all_tasks keys.
        # if a process is in forced_tasks it gets forced.
        forced_tasks = self.options.get(self.name, "")
        proc_str  = "Processing " + self.name
        message = "%s = %s. Forced tasks are: %s" %(proc_str,len(proc_str),forced_tasks)
        logger.debug(message)   
        for task, task_func, skippable in self.pending:
            if skippable and not should_process:
                continue
            # doing unskippable actions like extending python or env PATH.
            # or we should_process is True
            nice_func = task_func.strip("_")
            message = "\t-->performing %s for %s"%(nice_func, self.name)
            logger.debug(message) 
            success = getattr(self, task_func)()
            if success == Later:
                message = "\t-->%s for %s we be done later"%(nice_func, self.name)
                logger.debug(message) 
            elif success == False:
                message = "\t-->%s for %s failed"%(nice_func, self.name)
                logger.debug(message)
                if not should_process:
                    message = "-o %s was specified, ignoring error on package %s"% \
                         (self.options.get("only"), self.name)
                    logger.debug(message)
                    continue
                return False
            else:
                self.task_is_done(self.name, task)
        make_silent(False)
        return True

    def _download(self):
        # a proj with a none url implicitely means
        # the sources are already here because some
        # other proj installed it.
        if self.download_url is None:
            return True    
        dir=self._get_dl_path()
        if self.download_name in os.listdir(dir):
            message = "%s already downloaded!" %self.download_name
            logger.debug(message) 
            return True
        else:
            ret = url(self.download_url, dir=self._get_dl_path(), dl_name=self.download_name)
            return ret
    
    def _unpack(self, arch=None):
        # a proj with a none url implicitely means
        # the sources are already here because some
        # other proj installed it.
        if self.download_url is None:
            logger.debug("No url")
            ret = True
        if exists(self.sourcedir):
            message =  'already unpacked in %s' %repr(self.sourcedir)
            logger.debug(message)
            ret = True
        else:
            arch = arch or self.archname
            ret = unpack(arch, self.sourcedir)
        
        self._fix_source_dir()
        return ret 

    def _fix_source_dir(self):
        if self.archive_subdir:
            if not self._source_dir_fixed:
                old_sourcedir = self.sourcedir
                try:
                    message =  "fixing sourcedir %s" %self.sourcedir
                    logger.debug(message)               
                    self.sourcedir = into_subdir(self.sourcedir, self.archive_subdir)
                    if self.sourcedir is None:
                        self.sourcedir = old_sourcedir
                        raise Exception("Subdir should exist but doesn't, archive has probably not been unpacked")
                except:
                    traceback.print_exc()
                    return False
                else:
                    return True
                self._source_dir_fixed = True

    def _extend_sys_path(self):
        exp = self.extra_paths()
        if exp is not None:
            if isinstance(exp, tuple):
                exp = sj(exp)
            os.environ["PATH"] = sj([exp,os.environ["PATH"]])
        return True

    def _extend_python_path(self):
        exp = self.extra_python_paths()
        if exp is not None:
            if isinstance(exp, tuple):
                sys.path.extend(exp)
                exp = sj(exp)
            elif isinstance(exp, str):
                sys.path.extend(exp.split(os.pathsep))
            os.environ["PYTHONPATH"] = sj([exp,os.environ.get("PYTHONPATH","")])
        return True

    # -- Top level process, they delegate to abstract methods, try not to override --
    @in_dir("sourcedir")
    @try_except
    def _configure(self):
        #self._fix_source_dir()

        return self.configure()
        
    @in_dir("sourcedir")
    @try_except
    def _make(self):
        return self.make()
    
    @in_dir("sourcedir")
    @try_except
    def _patch(self):
        return self.patch()
        
    @in_dir("sourcedir")
    @try_except
    def _install(self):
        return self.install()
        
    @try_except
    def _configure_script(self):
        with open( self.setup_in_name, "r") as input, \
             open( self.setup_out_name, "w") as output:
            conf = self.default_substitutions.copy()
            conf.update(self.setup())
            conf = dict( (k,repr(v)) for k,v in conf.iteritems() )
            template = TemplateStr(input.read())
            output.write(template.substitute(conf))
        return True

    @in_dir("eggdir")
    @try_except
    def _bdist_egg(self):
        ret = self._configure_script()
    
        ret = ret & self.bdist_egg()
        
        # -- fix file name --
        eggname = self._glob_egg()
        dir_, filename = split(eggname)
        pyver   = "-py"+sys.winver
        archver = "-"+sys.platform
        if not self.py_dependent:
            filename = filename.replace(pyver, "")
        if not self.arch_dependent:
            filename = filename.replace(archver, "")
        os.rename(eggname, pj(dir_, filename))
        return ret

    @in_dir("eggdir")
    @try_except
    def _upload_egg(self):
        if not self.options["login"] or not self.options["passwd"]:
            self.use_cfg_login = True
            ret = self.upload_egg()
            if not ret:
                print "No login or passwd provided, skipping egg upload"
                return Later
            return ret
        return self.upload_egg()
        
    @in_dir("eggdir")
    @try_except
    def _copy_egg(self, dest_dir=None):
        if not dest_dir :
            dest_dir = self.options.get("dest_egg_dir")
        if not dest_dir:
            print "Will not place egg in a directory"
            return True

        eggname  = self._glob_egg()
        destname = pj(dest_dir, split(eggname)[1])
        if exists(destname):
            print "removing", destname
            os.remove(destname)
        print "copying", eggname, "to", destname
        shutil.copyfile(eggname, destname)
        return True

    def setup(self):
        if self.yet_installed:
            # for InstalledPackageEggBuilder
            # ie. if you use library yet installed (no-compilation)
            
            packages, package_dirs = self.find_packages_and_directories()
            
            install_dir = os.path.dirname(self.package.__file__)
            
            # py_modules = recursive_glob(self.install_dir, Pattern.pymod)
            data_files = recursive_glob_as_dict(install_dir,
                        ",".join(["*.example","*.txt",Pattern.pyext,"*.c",".1"])).items()

            d = dict ( PACKAGES = packages,
                       PACKAGE_DIRS = package_dirs,
                       DATA_FILES  = data_files,
                       LIB_DIRS         = None,
                       INC_DIRS         = None,
                       BIN_DIRS         = None,
                      )
            d.update(self.setup_2())
            return d  
        else:
            # for everything else
            ret = dict()
            
            lib = path(self.sourcedir)/'lib'
            inc = path(self.sourcedir)/'include'
            bin = path(self.sourcedir)/'bin'
            
            if lib.exists():
                ret['LIB_DIRS'] = {'lib' : pj(self.sourcedir,'lib') }
            else:
                ret['LIB_DIRS'] = None
            if inc.exists():
                ret['INC_DIRS'] = {'include' : pj(self.sourcedir,'include') }
            else:
                ret['INC_DIRS'] = None
            if bin.exists():
                ret['BIN_DIRS'] = {'bin' : pj(self.sourcedir,'bin') }
            else:
                ret['BIN_DIRS'] = None                
                
            return ret 
            # dict(
                        # LIB_DIRS         = {'lib' : pj(self.sourcedir,'lib') },
                        # INC_DIRS         = {'include' : pj(self.sourcedir,'include') },
                        # BIN_DIRS         = {'bin' : pj(self.sourcedir,'bin') },
                        # )
    
    # for InstalledPackageEggBuilder
    # ie. if you use library yet installed (no-compilation)
    def setup_2(self):
        raise NotImplementedError     

    # -- The ones you can override are these ones --
    def extra_paths(self):
        return None
        
    def extra_python_paths(self):
        return None
        
    def patch(self):
        return True        

    def configure(self):
        return True
        
    def make(self):
        try:
            cmd = "mingw32-make -j " + str(self.options["jobs"])
        except:
            cmd = "mingw32-make"
        logger.debug(cmd)  
        return sh( cmd ) == 0

    def install(self):
        return sh("mingw32-make install") == 0

    def _glob_egg(self):
        eggs = glob.glob( pj(self.eggdir, "dist", "*.egg") )
        if len(eggs) == 0:
            raise Exception("No egg found for "+self.egg_name())
        elif len(eggs) > 1:
            raise Exception("Found multiple eggs for "+self.egg_name()+reduce(lambda x,y:x+"\t->%s\n"%y, eggs, "\n"))
        return eggs[0]    
        
    def bdist_egg(self):
        #ret0 = sh(sys.executable + " setup.py egg_info --egg-base=%s"%self.eggdir ) == 0
        return sh(sys.executable + " setup.py bdist_egg") == 0

    def upload_egg(self):
        if not self.use_cfg_login:
            opts = self.options["login"], self.options["passwd"], \
                    self.egg_name(), "\"ThirdPartyLibraries\"", "vplants" if not self.options["release"] else "openalea"
            return sh(sys.executable + " setup.py egg_upload --yes-to-all --login %s --password %s --release %s --package %s --project %s"%opts) == 0
        else:
            opts = self.egg_name(), "\"ThirdPartyLibraries\"", "vplants" if not self.options["release"] else "openalea"
            return sh(sys.executable + " setup.py egg_upload --yes-to-all --release %s --package %s --project %s"%opts) == 0
    
    #################################
    ## Come from InstalledPackageEggBuilder
    #################################
    @property
    def package(self):
        return __import__(self.packagename)
    @property
    def module(self):
        if self.__modulename__:
            return __import__(".".join([self.packagename,self.__modulename__]),
                              fromlist=[self.__modulename__])
    @property
    def packagename(self):
        return self.__packagename__ or self.egg_name()

    def _filter_packages(self, pkgs):
        parpkg = self.packagename + "."
        return [ p for p in pkgs if (p == self.packagename or p.startswith(parpkg))]

    def find_packages(self):
        from setuptools import find_packages
        install_dir = os.path.dirname(self.package.__file__)
        pkgs   = find_packages( pj(install_dir, os.pardir) )
        pkgs = self._filter_packages(pkgs)
        return pkgs

    def find_packages_and_directories(self):
        pkgs = self.find_packages()
        dirs = {}
        install_dir = os.path.dirname(self.package.__file__)
        base = abspath( pj(install_dir, os.pardir) )
        for pk in pkgs:
            dirs[pk] =  pj(base, pk.replace(".", os.sep))
        return pkgs, dirs            
            
    #################################
    ## Come from BuildEnvironment
    #################################
    def get_working_path(self):
        return self.working_path
        
    def _get_dl_path(self):
        return pj( self.get_working_path(), "dl")
    
    def _get_src_path(self):
        return pj( self.get_working_path(), "src")
    
    def _get_install_path(self):
        return pj( self.get_working_path(), "install")
        
    def _get_egg_path(self):
        return pj( self.get_working_path(), "egg")
        
    def set_options(self, options):
        # TODO : to test if it works
        # maybe need to uncomment the 2 lines
        self.options = options.copy()
        self.tools = options.get("tools",[])[:]
        # Compiler.set_options(options) 
        # self.init()  
        
    def task_is_done(self, name, task):
        """ Marks that the `task` step has been accomplished for `proj`.
         - name is a key from M(Project|Egg)Builders.builders
         - task is a task identifier
        """
        if task not in self.done_tasks.setdefault(name, ""):
            self.done_tasks[name] += task

    def is_task_done(self, name, task):
        """ Tells is a task is finished. """
        return task in self.done_tasks.setdefault(name, "")

    def is_task_forced(self, name, task):
        """ Tells is the user forced this task. """
        return task in self.options.setdefault(name, "")
   