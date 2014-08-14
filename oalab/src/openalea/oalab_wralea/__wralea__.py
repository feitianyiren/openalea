# This file has been automatically generated by pkg_builder

from openalea.core import *

__name__ = 'openalea.OALab'
__version__ = '1.0.0'
__license__ = 'CeCILL-C'
__author__ = 'Julien Coste, Christophe Pradal'
__institutes__ = 'CIRAD, INRIA'
__description__ = ''
__url__ = 'http://openalea.gforge.inria.fr'

__editable__ = 'True'
__icon__ = ''
__alias__ = []

__all__ = []

worldreader = Factory( name="World reader",
              description="Read data from the data world.",
              category="oalab control",
              nodemodule="openalea.oalab_wralea.oalabnode",
              nodeclass="WorldReader",
              inputs = (dict(name='Key', interface=IStr),),
              outputs = (dict(name='Obj', interface=None),),
              lazy = False,
              
              )
    
__all__.append('worldreader')

worldwriter = Factory(name="World writer",
             description="Write data to the data world.",
             category="oalab control",
             nodemodule="openalea.oalab_wralea.oalabnode",
             nodeclass="WorldWriter",
             inputs = (dict(name='Key', interface=IStr),
                       dict(name='Obj', interface=None),),
             outputs = (dict(name='Obj', interface=None),),
             lazy = False,
             )

__all__.append('worldwriter')

world_rw = Factory(name="World setdefault",
             description="world.setdefault(key,value).",
             category="oalab control",
             nodemodule="openalea.oalab_wralea.oalabnode",
             nodeclass="WorldDefault",
             inputs = (dict(name='Key', interface=IStr),
                       dict(name='Value', interface=None),),
             outputs = (dict(name='Obj', interface=None),),
             lazy = False,
             )

__all__.append('world_rw')

controlreader = Factory( name="Control",
              description="Get the control object from the control manager.",
              category="oalab control",
              nodemodule="openalea.oalab_wralea.oalabnode",
              nodeclass="Control",
              inputs = (dict(name='Key', interface=IStr),),
              outputs = (dict(name='Obj', interface=None),),
              lazy = False,
              
              )
    
__all__.append('controlreader')

scene_2_geom = Factory(name='Scene to Geometry',
                authors='F. Boudon, C. Pradal, J. Coste(wralea authors)',
                description='Extract geometry from scene',
                category='Data I/O',
                nodemodule='openalea.oalab_wralea.oalabnode',
                nodeclass='Scene2Geom',
                inputs=None,
                outputs=None,
               )
               
__all__.append('scene_2_geom')

geom_2_scene = Factory(name='Geometry to Scene',
                authors='F. Boudon, C. Pradal, J. Coste(wralea authors)',
                description='Create scene from geometry',
                category='Data I/O',
                nodemodule='openalea.oalab_wralea.oalabnode',
                nodeclass='Geom2Scene',
                inputs=(dict(name='geometry', interface=IStr)),
                outputs=(dict(name='Scene', interface=IStr)),
               )
               
__all__.append('geom_2_scene')