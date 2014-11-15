"""
Blender plugin to visualize particle-based simulation resultsa stored as 
an Unstructred Grid in the VTK-XML-Fileformat.
author:diehlpk
date: 13.10.2014
"""
bl_info = {
	"name":	"VTK-Importer",
	"author": "diehlpk",
	"blender": (2, 6, 9),
	"version": (0, 0, 1),
	"location": "File > Import-Export",
	"description": "Import VTK unstructured grid",
	"category": "Import-Export"
}

# Imports for readinf vtk
from xml.etree import ElementTree
import re

# Import blender addon api
import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (StringProperty,
					BoolProperty,
					EnumProperty,
					IntProperty,
					FloatProperty)


def addParticle(x, y, z, r):
	"""Adds a primitive uV sphere to the blender engine
	@param x X coordinate of the center of the sphere
	@param y Y coordinate of the center of the sphre
	@param z Z Coordinate of the center of the sphre
	@param r Radius of the sphere
	"""
	bpy.ops.mesh.primitive_uv_sphere_add(
		segments=6,
		ring_count=6,
		size=r,
		location=(x, y, z),
		rotation=(0, 0, 0),
		layers=(
			True, False, False, False, False, False, False, False,
			False, False, False, False, False, False, False, False,
			False, False, False, False
		)
	)

def ValueToRGB(minimum, maximum, value):
	""" Converts the value to a RGB map
	@param minimum The minimum of all values
	@param maximum The maximum of all values
	@param value The value
	"""
	minimum , maximum = float(minimum), float(maximum)
	ratio = 2 * (value-minimum) / (maximum-minimum)
	b = int(max(0,255*(1-ratio)))
	r = int(max(0,255*(1-ratio)))
	g = 255 - b - r
	return r, g, b

class ImportVTK(Operator, ImportHelper):

	"""VTK unstructured grid importer"""
	bl_idname = "import.vtk"
	bl_label = "VTK importer"

	filepath = bpy.props.StringProperty(subtype="FILE_PATH")

	def __init__(self):
		pass

	@classmethod
	def poll(cls, context):
		return context.object is not None

	def execute(self, context):

		"""Configuration"""
		radius = 0.01
		name = "1DColor"

		bpy.ops.object.select_all(action='DESELECT')

		addParticle(0, 0, 0, radius)
		self.sphere = bpy.context.object
		self.sphere.name = 'vtk_import_root_object'

		points = []
		material = []

		with open(self.filepath, 'r') as f:
			tree = ElementTree.parse(f)
	
		for node in tree.getiterator('DataArray'):
			if (node.attrib.get('Name') == 'Points' or node.attrib.get('Name') == 'coordinates'):

				dim = int(node.attrib.get('NumberOfComponents'))
				text = re.sub("\n", "", node.text)
				text = re.sub("\t", "", text)
				text = re.sub(" +", " ", text)
				text = text.lstrip(' ').rstrip(' ')
				splitted = text.split(' ')
				pos = []
				for element in splitted:
					pos.append(element)
					if (len(pos) == dim):
						points.append(pos)
						pos = []

			if (node.attrib.get('Name') == name and len(name) > 0 ):
				dim = int(node.attrib.get('NumberOfComponents'))
				colors = []
				if(dim == 1):
					text = re.sub(" +" , "" , node.text)
					text = re.sub(" ", "" , text)
					text = re.sub("\t", "" , text)
					text = text.lstrip().rstrip()
					splitted = text.split("\n")
					for element in splitted:
						colors.append(float(element))
						
					minimum = min(colors)
					maximum = max(colors)

					for i in range(len(colors)):
						m = bpy.data.materials.new(str(i))
						m.diffuse_color = ValueToRGB(minimum,maximum,colors[i])
						material.append(m)
				#if(dim == 3):	
				#	text = re.sub("\n", "", node.text)
				#	text = re.sub("\t", "", text)
				#	text = re.sub(" +", " ", text)
				#	text = text.lstrip(' ').rstrip(' ')
				#	splitted = text.split(' ')
				#	color = []
				#	for element in splitted:
				#		pos.append(element)
				#		if (len(color) == dim):
				#			colors.append(color)
				#			color = []
		index = 0
		for i in range(len(points)):
				
			ob = self.sphere.copy()
			ob.name = 'particle_' + str(index)
			ob.data = self.sphere.data.copy()
			pos = points[i]
			ob.location = (float(pos[0]), float(pos[1]), float(pos[2]))
			bpy.context.scene.objects.link(ob)
			ob.data.materials.append(material[i])
			index = index + 1
				
		bpy.ops.object.select_all(action='DESELECT')
		bpy.ops.object.select_pattern(pattern='vtk_import_root_object',case_sensitive=False, extend=False)
		bpy.ops.object.delete()

		bpy.context.scene.update()

		return {'FINISHED'}

	def invoke(self, context, event):
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}


def menu_func(self, context):
	self.layout.operator(ImportVTK.bl_idname, text="VTK Importer")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
	register()
