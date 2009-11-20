# -*- python -*-
#
#       OpenAlea.Visualea: OpenAlea graphical user interface
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Daniel Barbeau <daniel.barbeau@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
"""Generic Graph Widget"""

__license__ = "Cecill-C"
__revision__ = " $Id$ "


import weakref, types
from PyQt4 import QtGui, QtCore
from openalea.core.settings import Settings

from . import grapheditor_baselisteners, grapheditor_interfaces
import edgefactory

from math import sqrt


#__Application_Integration_Keys__
__AIK__ = [
    "mouseMoveEvent",
    "mouseReleaseEvent",
    "mousePressEvent",
    "mouseDoubleClickEvent",
    "keyReleaseEvent",
    "keyPressEvent",
    "contextMenuEvent"
    ]


def myShowToolTip(*args):
    print args
    
#------*************************************************------#
class QtGraphViewElement(grapheditor_baselisteners.GraphElementObserverBase):
    """Base class for elements in a QtGraphView.

    Implements basic listeners calls for elements of a graph.
    A listener call is the method that is called after the main
    listening method (self.notify) dispatches the events. They
    are specified by grapheditor_interfaces.IGraphViewElement.

    The class also implements a mecanism to easily override user
    events from the client application. What does this mean? In this
    framework, the graph editor starts as a simple graph listener. The
    current module extends those listeners to be able to react to the
    events and produce a QGraphicsView of the graph with graph-specific
    interactions. The dataflowview module extends the current module 
    to handle dataflows. However these extensions are not client-specific.
    There is nothing related for example specifically to Visualea.
    by using QtGraphViewVertex.set_event_handler(key, handler), or even on
    specialised elements like
    dataflowview.strat_vertex.GraphicalVertex.set_event_handler(key, handler),
    one can bind a specific behaviour to the event named by \"key\". The
    handler will be specific to the class set_event_handler was called on
    (hopefully).

    :Listener calls:
        * position_changed(self,  (posx, posy))
        * add_to_view(self, view)
        * remove_from_view(self, view)

    """

    ####################################
    # ----Class members come first---- #
    ####################################
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    @classmethod
    def set_event_handler(cls, key, handler):
        """Let handler take care of the event named by key.

        :Parameters:
            - key (str) - The name of the event.
            - handler (callable) - The handler to register with key.


         The key can be any of
           * \"mouseMoveEvent\"
           * \"mouseReleaseEvent\"
           * \"mousePressEvent\"
           * \"mouseDoubleClickEvent\"
           * \"keyReleaseEvent\"
           * \"keyPressEvent\"
           * \"contextMenuEvent\"

        See the Qt documentation of those to know the expected signature
        of the handler (usually : handlerName(QObject, event)).
          
        """
        if key in cls.__application_integration__:
            cls.__application_integration__[key]=handler


    ####################################
    # ----Instance members follow----  #
    ####################################    
    def __init__(self, observed=None, graph=None):
        """
        :Parameters:
             - observed (openalea.core.observer.Observed) - The item to
             observe.
             - graph (ducktype) - The graph owning the item.

        """
        grapheditor_baselisteners.GraphElementObserverBase.__init__(self, 
                                                                    observed, 
                                                                    graph)

        #we bind application overloads if they exist
        #once and for all. As this happens after the
        #class is constructed, it overrides any method
        #called "name" with an application-specific method
        #to handle events.
        for name, hand in self.__application_integration__.iteritems():
            if "Event" in name and hand:
                setattr(self, name, types.MethodType(hand,self,self.__class__))

    #################################
    # IGraphViewElement realisation #
    #################################       
    def add_to_view(self, view):
        """An element adds itself to the given view"""
        view.addItem(self)

    def remove_from_view(self, view):
        """An element removes itself from the given view"""
        view.removeItem(self)

    def position_changed(self, *args):
        """Updates the item's **graphical** position from
        model notifications. """
        point = QtCore.QPointF(args[0], args[1])
        self.setPos(point)




#------*************************************************------#
class QtGraphViewVertex(QtGraphViewElement):
    """An abstract graphic item that represents a graph vertex.

    The actual implementation is done in the derived class. What this
    intermediate implementation does is that it provides the basics
    for handling edge creation from one node to the other.
    It also provides a state based pluggable painting system,
    meant to customize the painting from the application side.
    Of course, if it doesn't match your needs you
    can override it completely in your subclass."""
    
    ####################################
    # ----Class members come first---- #
    ####################################
    __state_drawing_strategies__={}

    @classmethod
    def add_drawing_strategies(cls, d):
        """Adds the drawing strategies in d.
        
        :Parameters:
            - d (dict) - a mapping from states (any comparable type)
            to drawing strategies. Drawing strategies must implement
            the grapheditor_interfaces.IGraphViewVertexPaintStrategy
            interface.

         """
        for k, v in d.iteritems():
            if(grapheditor_interfaces.IGraphViewVertexPaintStrategy.check(v)):
                cls.__state_drawing_strategies__[k] = v

    @classmethod
    def get_drawing_strategy(cls, state):
        """Get a strategy for a given state.

        :Returns Type:
        Something that looks verifies IGraphViewVertexPaintStrategy.
        """
        return cls.__state_drawing_strategies__.get(state)
    
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )


    ####################################
    # ----Instance members follow----  #
    ####################################    
    def __init__(self, vertex, graph):
        """
        :Parameters:
            - vertex - the vertex to observe.
            - graph - the owner of the vertex

        """
        QtGraphViewElement.__init__(self, vertex, graph)
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)        
        return

    def vertex(self):
        """retreive the vertex"""
        return self.observed()

    def get_center(self):
        center = self.rect().center()
        center = self.mapToScene(center)
        return [center.x(), center.y()]

    def set_highlighted(self, value):
        pass


    #####################
    # ----Qt World----  #
    #####################
    # ---> state-based painting
    def select_drawing_strategy(self, state):
        """This method gets called by the painting process to
        determine what strategy should handle a given state.
        The default behaviour just calls the get_drawing_strategy
        classmethod. Reimplement to customize the state drawing.
        """
        return self.get_drawing_strategy(state)

    def paint(self, painter, option, widget):
        """Qt-specific call to paint things."""
        paintEvent=None #remove this
        path=None
        firstColor=None
        secondColor=None
        gradient=None

        #FINDING THE STRATEGY
        state = self.vertex().get_state()
        strategy = self.select_drawing_strategy(state)
        if(strategy):
            fullCustom = strategy.paint(self, painter, option, widget)
            if(fullCustom): return
            path = strategy.get_path(self)
            gradient=strategy.get_gradient(self)
            #the gradient is already defined, no need for colors
            if(not gradient):
                firstColor=strategy.get_first_color(self)
                secondColor=strategy.get_second_color(self)
        else: #...or fall back on defaults
            rect = self.rect()
            path = QtGui.QPainterPath()
            path.addRoundedRect(rect, 5, 5)
            firstColor = self.not_selected_color
            secondColor = self.not_modified_color

        if(not gradient):
            gradient = QtGui.QLinearGradient(0, 0, 0, 100)
            gradient.setColorAt(0.0, firstColor)
            gradient.setColorAt(0.8, secondColor)

        #PAINTING
        painter.setBackgroundMode(QtCore.Qt.TransparentMode)
        if(strategy):
            strategy.prepaint(self, paintEvent, painter, state)
        #shadow drawing:
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(100, 100, 100, 50))
        painter.drawPath(path)
        #item drawing
        painter.setBrush(QtGui.QBrush(gradient))        
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.drawPath(path)

        if(strategy):
            strategy.postpaint(self, paintEvent, painter, state)

        #selection marker is drawn at the end
        if(self.isSelected()):
            painter.setPen(QtCore.Qt.DashLine)
            painter.setBrush(QtGui.QBrush())
            painter.drawRect(self.rect())

    # ---> other events
    def polishEvent(self):
        """Qt-specific call to handle events that occur on polishing phase.
        Default updates the model's ad-hoc position value."""
        point = self.scenePos()
        cPos = point + self.rect().center()
        self.vertex().get_ad_hoc_dict().set_metadata('connectorPosition',
                                                     [cPos.x(), cPos.y()])
        self.vertex().get_ad_hoc_dict().set_metadata('position', 
                                                       [point.x(), point.y()], False)

    def moveEvent(self, event):
        """Qt-specific call to handle events that occur on item moving.
        Default updates the model's ad-hoc position value."""
        point = event.newPos()
        cPos = point + self.rect().center()
        self.vertex().get_ad_hoc_dict().set_metadata('connectorPosition',
                                                     [cPos.x(), cPos.y()])
        self.vertex().get_ad_hoc_dict().set_metadata('position', 
                                                     [point.x(), point.y()])

    def mousePressEvent(self, event):
        """Qt-specific call to handle mouse clicks on the vertex.
        Default implementation initiates the creation of an edge from
        the vertex."""
        graphview = self.scene().views()[0]
        if (graphview and event.buttons() & QtCore.Qt.LeftButton and
            event.modifiers() & QtCore.Qt.ControlModifier):
            pos = [event.scenePos().x(), event.scenePos().y()]
            graphview.new_edge_start(pos)
            return



#------*************************************************------#
class QtGraphViewAnnotation(QtGraphViewElement):
    """An abstract graphic item that represents a graph annotation"""

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, annotation, graph):
        """
        :Parameters:
            - annotation - The annotation object to watch.
            - graph      - The owner of the annotation

        """
        QtGraphViewElement.__init__(self, annotation, graph)
        return

    def annotation(self):
        """Access to the annotation"""
        return self.observed()

    def notify(self, sender, event):
        """Model event dispatcher.
        Intercepts the \"MetaDataChanged\" event with the \"text\" key
        and redirects it to self.set_text(self). Any other event
        if processed by the superclass' notify method."""
        if(event[0] == "MetaDataChanged"):
            if(event[1]=="text"):
                if(event[2]): self.set_text(event[2])

        QtGraphViewElement.notify(self, sender, event)


    # ---->controllers
    def mouseDoubleClickEvent(self, event):
        """ todo """
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setSelected(True)
        self.setFocus()
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        self.setTextCursor(cursor)

    def focusOutEvent(self, event):
        """ todo """
        self.setFlag(QtGui.QGraphicsItem.ItemIsFocusable, False)

        # unselect text
        cursor = self.textCursor ()
        if(cursor.hasSelection()):
            cursor.clearSelection()
            self.setTextCursor(cursor)
            
        self.annotation().get_ad_hoc_dict().set_metadata('text', str(self.toPlainText()))

        self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)




#------*************************************************------#
class QtGraphViewEdge(QtGraphViewElement):
    """Base class for Qt based edges."""

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, edge=None, graph=None, src=None, dest=None):
        QtGraphViewElement.__init__(self, edge, graph)

        self.setFlag(QtGui.QGraphicsItem.GraphicsItemFlag(
            QtGui.QGraphicsItem.ItemIsSelectable))
        
        self.src = None
        self.dst = None

        if(src)  : 
            self.initialise(src)
            self.src = weakref.ref(src)
        if(dest) : 
            self.initialise(dest)
            self.dst = weakref.ref(dest)

        self.sourcePoint = QtCore.QPointF()
        self.destPoint = QtCore.QPointF()

        self.__edge_path = None
        self.set_edge_path(edgefactory.EdgeFactory())
        self.setPen(QtGui.QPen(QtCore.Qt.black, 3,
                               QtCore.Qt.SolidLine,
                               QtCore.Qt.RoundCap,
                               QtCore.Qt.RoundJoin))

    def edge(self):
        if isinstance(self.observed, weakref):
            return self.observed()
        else:
            return self.observed

    def set_edge_path(self, path):
	self.__edge_path = path
        path = self.__edge_path.get_path(self.sourcePoint, self.destPoint)
        self.setPath(path)
        
    def update_line_source(self, *pos):
        self.sourcePoint = QtCore.QPointF(*pos)
        self.__update_line()

    def update_line_destination(self, *pos):
        self.destPoint = QtCore.QPointF(*pos)
        self.__update_line()

    def __update_line(self):
        path = self.__edge_path.get_path(self.sourcePoint, self.destPoint)
        self.setPath(path)

    def notify(self, sender, event):
        if(event[0] == "MetaDataChanged"):
            if(event[1]=="connectorPosition"):
                    pos = event[2]
                    if(sender==self.src()): 
                        self.update_line_source(*pos)
                    elif(sender==self.dst()):
                        self.update_line_destination(*pos)
            elif(event[1]=="hide" and sender==self.dst()):
                if event[2]:
                    self.setVisible(False)
                else:
                    self.setVisible(True)

    def initialise_from_model(self):
        self.src().get_ad_hoc_dict().simulate_full_data_change()
        self.dst().get_ad_hoc_dict().simulate_full_data_change()


    def remove(self):
        view = self.scene().views()[0]
        print "generic edge removal", self.src(), self.dst()
        view.graph().remove_edge(self.src(), self.dst())
        

    ############
    # Qt World #
    ############
    def shape(self):
        path = self.__edge_path.shape()
        if not path:
            return QtGui.QGraphicsPathItem.shape(self)
        else:
            return path

    def itemChange(self, change, value):
        """ Callback when item has been modified (move...) """

        if (change == QtGui.QGraphicsItem.ItemSelectedChange):
            if(value.toBool()):
                color = QtCore.Qt.blue
            else:
                color = QtCore.Qt.black

            self.setPen(QtGui.QPen(color, 3,
                                   QtCore.Qt.SolidLine,
                                   QtCore.Qt.RoundCap,
                                   QtCore.Qt.RoundJoin))
                
        return QtGui.QGraphicsItem.itemChange(self, change, value)



class QtGraphViewFloatingEdge( QtGraphViewEdge ):

    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )

    def __init__(self, srcPoint, graph):
        QtGraphViewEdge.__init__(self, None, graph, None, None)
        self.sourcePoint = QtCore.QPointF(*srcPoint)

    def notify(self, sender, event):
        return

    def consolidate(self, graph):
        try:
            srcVertex, dstVertex = self.get_connections()
            if(srcVertex == None or dstVertex == None):
                return
            graph.add_edge(srcVertex, dstVertex)
        except Exception, e:
            print "consolidation failed :", e
        return
        
    def get_connections(self):
        #find the vertex items that were activated
        srcVertexItem = self.scene().itemAt( self.sourcePoint )
        dstVertexItem = self.scene().itemAt( self.destPoint   )

        view = self.scene().views()[0]

        if( type(dstVertexItem) not in view.connector_types or
            type(dstVertexItem) not in view.connector_types):
            return None, None

        #if the input and the output are on the same vertex...
        if(srcVertexItem == dstVertexItem):
            raise Exception("Nonsense connection : plugging self to self.")            

        return srcVertexItem.vertex(), dstVertexItem.vertex()



#------*************************************************------#
class QtGraphView(QtGui.QGraphicsView, grapheditor_baselisteners.GraphListenerBase):
    """A Qt implementation of GraphListenerBase    """

    ####################################
    # ----Class members come first---- #
    ####################################
    __application_integration__= dict( zip(__AIK__,[None]*len(__AIK__)) )
    __application_integration__["mimeHandlers"]={}
    __application_integration__["pressHotkeyMap"]={}
    __application_integration__["releaseHotkeyMap"]={}

    __defaultDropHandler = None
    
    @classmethod
    def set_mime_handler_map(cls, mapping):
        cls.__application_integration__["mimeHandlers"].update(mapping)

    @classmethod
    def set_keypress_handler_map(cls, mapping):
        cls.__application_integration__["pressHotkeyMap"] = mapping

    @classmethod
    def set_keyrelease_handler_map(cls, mapping):
        cls.__application_integration__["releaseHotkeyMap"] = mapping

    @classmethod
    def set_default_drop_handler(cls, handler):
        cls.__defaultDropHandler = handler


    ####################################
    # ----Instance members follow----  #
    ####################################   
    def __init__(self, parent, graph):
        QtGui.QGraphicsView.__init__(self, parent)
        grapheditor_baselisteners.GraphListenerBase.__init__(self, graph)


        #we bind application overloads if they exist
        #once and for all. As this happens after the
        #class is constructed, it overrides any method
        #called "name" with an application-specific method
        #to handle events.
        for name, hand in self.__application_integration__.iteritems():
            if "Event" in name and hand:
                setattr(self, name, types.MethodType(hand,self,self.__class__))

        self.__selectAdditions=False
        
        scene = QtGui.QGraphicsScene(self)
        self.setScene(scene)

        # ---Custom tooltip system---
        self.__tooltipTimer = QtCore.QTimer()
        self.__tooltipTimer.setInterval(800)
        self.connect(self.__tooltipTimer, QtCore.SIGNAL("timeout()"),
                     self.tooltipTrigger)
        self.__tooltipPos = None


        # ---Qt Stuff---
        #self.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        self.setCacheMode(QtGui.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtGui.QGraphicsView.AnchorViewCenter)
        self.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.rebuild_scene()

        



    def get_scene(self):
        return self.scene()

    ##################
    # QtWorld-Events #
    ##################
    def tooltipTrigger(self):
#         print self.itemAt(self.__tooltipPos)
#         print "tooltip now!"
        self.__tooltipTimer.stop()
    
    def wheelEvent(self, event):
        #self.centerOn(QtCore.QPointF(event.pos()))
        delta = -event.delta() / 2400.0 + 1.0
        self.scale_view(delta)

    def mouseMoveEvent(self, event):
#        self.__tooltipTimer.stop()
        if(self.is_creating_edge()):
            pos = self.mapToScene(event.pos())
            pos = [pos.x(), pos.y()]
            self.new_edge_set_destination(*pos)
            return
#         elif(event.buttons()==QtCore.Qt.NoButton):
#             self.__tooltipTimer.start()
#             self.__tooltipPos = event.pos()
#             return
        QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        if(self.is_creating_edge()):
            self.new_edge_end()
        QtGui.QGraphicsView.mouseReleaseEvent(self, event)

    def accept_event(self, event):
        """ Return True if event is accepted """
        for format in self.__application_integration__["mimeHandlers"].keys():
            if event.mimeData().hasFormat(format): return format
        return True if self.__defaultDropHandler else False

    def dragEnterEvent(self, event):
        event.setAccepted(True if self.accept_event(event) else False)
            
    def dragMoveEvent(self, event):
        format = self.accept_event(event)
        if (format):
            event.setDropAction(QtCore.Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        format = self.accept_event(event)
        handler = self.__application_integration__["mimeHandlers"].get(format)
        if(handler):
            handler(self, event)
        else:
            self.__defaultDropHandler(event)
        

        QtGui.QGraphicsView.dropEvent(self, event)

    def keyPressEvent(self, event):
        combo = event.modifiers().__int__(), event.key()
        action = self.__application_integration__["pressHotkeyMap"].get(combo)
        if(action):
            action(self, event)
        else:
            QtGui.QGraphicsView.keyPressEvent(self, event)

    def keyReleaseEvent(self, event):
        combo = event.modifiers().__int__(), event.key()
        action = self.__application_integration__["releaseHotkeyMap"].get(combo)
        if(action):
            action(self, event)
        else:
            QtGui.QGraphicsView.keyReleaseEvent(self, event)

#     def viewportEvent(self, event):
#         etype = event.type()
#         if(etype==QtCore.QEvent.ToolTip): #we handle tooltips our own way
#             return True
#         else:
#             return QtGui.QGraphicsView.viewportEvent(self, event)


    #########################
    # Other utility methods #
    #########################
    def scale_view(self, factor):
        self.scale(factor, factor)

    def rebuild_scene(self):
        """ Build the scene with graphic vertex and edge"""
        self.clear_scene()
        self.graph().simulate_construction_notifications()

    def clear_scene(self):
        """ Remove all items from the scene """
        scene = QtGui.QGraphicsScene(self)
        self.setScene(scene)

    def new_edge_scene_cleanup(self, graphicalEdge):
        self.scene().removeItem(graphicalEdge)

    def new_edge_scene_init(self, graphicalEdge):
        self.scene().addItem(graphicalEdge)

    def get_selected_items(self, subcall=None, vertices=True):
        """ """
        if(subcall):
            return [ eval("item."+subcall) for item in self.items() if item.isSelected() and
                     isinstance(item, QtGraphViewVertex)]
        elif(vertices):
            return [ item for item in self.items() if item.isSelected() and 
                     isinstance(item, QtGraphViewVertex)]
        else:
            return [ item for item in self.items() if item.isSelected()]

                     
    def get_selection_center(self, selection=None):
        items = None
        if selection:
            items = selection
        else:
            items = self.get_selected_items()

        l = len(items)
        if(l == 0) : return QtCore.QPointF(30,30)
        
        sx = sum((i.pos().x() for i in items))
        sy = sum((i.pos().y() for i in items))
        return QtCore.QPointF( float(sx)/l, float(sy)/l )

    def select_added_elements(self, val):
        self.__selectAdditions=val

    def post_addition(self, element):
        """defining virtual bases makes the program start
        but crash during execution if the method is not implemented, where
        the interface checking system could prevent the application from
        starting, with a die-early behaviour."""
        if(self.__selectAdditions):
            element.setSelected(True)

    def find_closest_connectable(self, pos):
        boxsize = 10.0
        #creation of a square which is a selected zone for while ports 
        rect = QtCore.QRectF((pos[0] - boxsize/2), (pos[1] - boxsize/2), boxsize, boxsize);
        dstPortItems = self.scene().items(rect)      
        dstPortItems = [item for item in dstPortItems if item.__class__ in self.connector_types]

        distance = float('inf')
        dstPortItem = None
        for item in dstPortItems:
            d = sqrt((item.boundingRect().center().x() - pos[0])**2 + 
                        (item.boundingRect().center().y() - pos[1])**2)
            if d < distance:
                distance = d
                dstPortItem = item            

        return dstPortItem

        

