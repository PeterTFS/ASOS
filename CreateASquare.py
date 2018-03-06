"""
Write a script that creates a new polygon feature class containing a
single ( square ) polygon with the following coordinates: ( 0, 0 ), ( 0, 1,000 ),
( 1,000, 0 ), and ( 1,000, 1,000 ).
"""
# import arcpy

# fc = "c:/Temp/psa.gdb/polygon2"
# cursor = arcpy.da.InsertCursor(fc, ["SHAPE@"])
# # Create a polygon geometry
# array = arcpy.Array([arcpy.Point(0, 0),
#                      arcpy.Point(0, 1000),
#                      arcpy.Point(1000, 1000),
#                      arcpy.Point(1000, 0)
#                      ])
# polygon = arcpy.Polygon(array)

# cursor.insertRow([polygon])
# # #
# print polygon
# Open an InsertCursor and insert the new geometry
# cursor = arcpy.da.InsertCursor(
#     r'C:\Temp\psa.gdb', ['SHAPE@'])
# cursor.insertRow([polygon])

# Delete cursor object
#del cursor
# outpath = "c:\Temp"
# newfc = "polygon.shp"
# arcpy.CreateFeatureclass_management(outpath, newfc, "Polygon")

# cursor = arcpy.da.InsertCursor(newfc, ["SHAPE@"])

# del cursor
# Import system modules

# import arcpy

# # Set workspace
# arcpy.env.workspace = "C:/Temp"

# # Set local variables
# out_path = "C:/Temp"
# out_name = "habitatareas.shp"
# geometry_type = "POLYGON"
# template = "tx_county.shp"
# has_m = "DISABLED"
# has_z = "DISABLED"

# # Use Describe to get a SpatialReference object
# spatial_reference = arcpy.Describe(
#     "C:/Temp/tx_county.shp").spatialReference

# # Execute CreateFeatureclass
# arcpy.CreateFeatureclass_management(
#     out_path, out_name, geometry_type, template,has_m, has_z, spatial_reference)


# from ete2 import Treedi
"""
Write two Python functions to find the minimum number in a list. The first function should compare each number to every other number on the list. O(n2)
. The second function should be linear O(n).
"""
