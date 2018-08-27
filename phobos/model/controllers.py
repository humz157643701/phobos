#!/usr/bin/python
# coding=utf-8

"""
Copyright 2014, University of Bremen & DFKI GmbH Robotics Innovation Center

This file is part of Phobos, a Blender Add-On to edit robot models.

Phobos is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License
as published by the Free Software Foundation, either version 3
of the License, or (at your option) any later version.

Phobos is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Phobos.  If not, see <http://www.gnu.org/licenses/>.

File controllers.py

Created on 24.08.2018

@author: Simon V. Reichel
"""


import bpy
import mathutils
from phobos import defs
from phobos.phoboslog import log
import phobos.utils.blender as bUtils
import phobos.utils.selection as sUtils
import phobos.utils.naming as nUtils
import phobos.utils.editing as eUtils
import phobos.utils.io as ioUtils


def deriveController(obj):
    import phobos.model.models as models
    props = models.initObjectProperties(obj, phobostype='controller')

    # return None if no controller is found (there will always be at least a name in the props)
    if len(props) < 2:
        return None

    if not obj.parent or obj.parent.phobostype not in defs.controllabletypes:
        log(("Can not derive controller from {}. " +
             "Insufficient requirements from parent object!").format(obj.name), 'ERROR')
        return None

    props['target'] = nUtils.getObjectName(obj.parent)

    return {}


def createController(controller, reference, origin=mathutils.Matrix()):
    """This function creates a new controller specified by its parameters.

    Args:
        controller (dict): phobos representation of the new controller
        reference (bpy_types.Object): object to add a parent relationship to
        origin (mathutils.Matrix, optional): new controllers origin

    Returns:
        bpy.types.Object -- new created controller object
    """
    layers = defs.layerTypes['controller']
    bUtils.toggleLayer(layers, value=True)

    # create controller object
    if controller['shape'].startswith('resource'):
        newcontroller = bUtils.createPrimitive(
            controller['name'], 'box', [1, 1, 1], layers,
            plocation=origin.to_translation(), protation=origin.to_euler(),
            pmaterial=controller['material'], phobostype='controller')
        # use resource name provided as: "resource:whatever_name"
        resource_obj = ioUtils.getResource(['controller'] +
                                           controller['shape'].split('://')[1].split('_'))
        if resource_obj:
            log("Assigned resource mesh and materials to new controller object.", 'DEBUG')
            newcontroller.data = resource_obj.data
            newcontroller.scale = (controller['size'],) * 3
        else:
            log("Could not use resource mesh for controller. Default cube used instead.", 'WARNING')
    else:
        newcontroller = bUtils.createPrimitive(
            controller['name'], controller['shape'], controller['size'], layers,
            plocation=origin.to_translation(), protation=origin.to_euler(),
            pmaterial=controller['material'], phobostype='controller')

    newcontroller.name = controller['name']
    newcontroller['controller/type'] = controller['type']

    # write the custom properties to the controller
    eUtils.addAnnotation(newcontroller, controller['props'], namespace='controller')

    # assign the parent if available
    if reference is not None:
        sUtils.selectObjects([newcontroller, reference], clear=True, active=1)

        if reference.phobostype == 'link':
            bpy.ops.object.parent_set(type='BONE_RELATIVE')
        else:
            bpy.ops.object.parent_set(type='OBJECT')

    return newcontroller
