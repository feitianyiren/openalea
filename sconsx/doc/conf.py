# This file is execfile()d with the current directory set to its containing dir.
import sys, os
import time
import ConfigParser


print 'Reading configuration file conf.py '

config = ConfigParser.RawConfigParser()
config.read('sphinx.ini')
name = config.get('metadata','package')
release = config.get('metadata','release')
version = config.get('metadata','version')
project = config.get('metadata','project')


# -----------------------------------------------------------------------------
#  NOTHING to CHANGE BELOW. Note that some options still have 'openalea' 
#  harcoded (e.g., the CSS filename.
# -----------------------------------------------------------------------------
Project = project.capitalize()
Name = name.capitalize()

# Get the year
year = time.ctime().split()[4]

# now check that we have the release 
try:
    print 'version found of %s package is %s ' % (name, release)
except NameError:
    'Please, provide the \'version\' variable within your setup.py file'

# This paths are required to access the extension and the import_modules.py file
sys.path.append(os.path.abspath('../../doc/sphinxext'))
sys.path.append(os.path.abspath('../../doc/sphinxext/numpyext'))
sys.path.append(os.path.abspath('./'+name))
sys.path.append(os.path.abspath('misc'))


# Sometimes, modules are not parsed (because a metaclass was found).
# import_modules.py contain a list of import that can be called to
# prevent errors when sphinx builds the inheritance diagram
# This paths are required to access the inheritance diagram extension
try:
    print 'importing modules'
    import import_modules   #created by sphinx_tools
except Exception,e:
    print e, 'Some imports failed in conf.py'

import ipython_console_highlighting


# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.autodoc', 
    'sphinx.ext.doctest', 
    'sphinx.ext.intersphinx',
    'inheritance_diagram', 
    'sphinx.ext.pngmath',
    'sphinx.ext.todo', 
    'numpydoc',
    'phantom_import', 
    'autosummary',
    'sphinx.ext.coverage',
    'only_directives'
    ]

todo_include_todos =True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['../../doc/.templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'contents'

# General information about the project.
project = unicode(project + '.' + name)
copyright = unicode('2009,'+ Project + '.' + Name)

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version
# The full version, including alpha/beta/rc tags.
try:
    indice = release.find('.', 2)
    version = release[0:indice]
except:
    version = release


# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['.build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
show_authors = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'openalea.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '../../doc/images/wiki_logo_openalea.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['.static', '../../doc/.static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

#content template for the index page.
html_index = 'index.html'

# Custom sidebar templates, maps page names to templates.
html_sidebars = {'index': 'indexsidebar.html'}
html_additional_pages = {'index': 'index.html'}
# If false, no module index is generated.
html_use_modindex = True

# If false, no index is generated.
html_use_index = True

# If true, the index is split into individual pages for each letter.
html_split_index = True

# If true, the reST sources are included in the HTML build as _sources/<name>.
html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = Project + 'doc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
    ('contents', 
     name + '.tex',
     unicode(Project + '.' + name + ' Documentation'),
     unicode(Project + ' consortium'), 
    'manual'),]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
latex_logo =  '../../doc/images/wiki_logo_openalea.png'

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

# Additional stuff for the LaTeX preamble.
latex_preamble = """
   \usepackage{amsmath}
   \usepackage{amsfonts}
   \usepackage{amssymb}
   \usepackage{txfonts}
"""



# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/dev': None}
intersphinx_mapping = {'file:///home/cokelaer/Work/eclipse_env/openalea/core/doc/html': None}
