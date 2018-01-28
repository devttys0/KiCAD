#!/usr/bin/python

import os
import sys
import xml.etree.ElementTree as xml

def is_part_number(field, allowed=[]):
   '''
   Heuristic identification of part number fields in KiCAD.
   '''
   field_name = field.attrib["name"].lower()
   if (len([x for x in allowed if x in field_name]) > 0 and
       "part" in field_name and
       ("#" in field_name or "number" in field_name or "no." in field_name)):
      return True
   return False

def is_supplier_part_number(field):
   return is_part_number(field, ["suppl", "vend"])

def is_manufacturer_part_number(field):
   return is_part_number(field, ["manuf"])

retval = 0
component_count = 0
bom = {}

try:
   xml_file = sys.argv[1]
   out_file_name = os.path.join(os.path.dirname(xml_file), "digikey_bom.csv")
except Exception as e:
   sys.stderr.write("Cmdline Usage: %s <input XML file>n" % sys.argv[0])
   sys.stderr.write("KiCAD Usage:   %s %%I\n" % sys.argv[0])
   sys.exit(1)
   
try:

   out_file = open(out_file_name, "wb")
except Exception as e:
   sys.stderr.write("Failed to open %s for writing: %s\n" % (out_file_name, str(e)))
   sys.exit(-1)

tree = xml.parse(xml_file)
root = tree.getroot()

# Get the XML root
for child in root:

   # Find the components tag
   if child.tag == "components":

      # Find each "comp" tag
      for comp in child:
         # Be sure to initialize this to None
         component_reference = None
         if comp.tag == "comp":
            part_number = None
            component_reference = comp.attrib["ref"].strip()

            # Look through each comp tag for a fields tag
            for grandchild in comp:
               if grandchild.tag == "fields":

                  # Look through each fields tag for a valid field tag
                  # that looks like a vendor part number field.
                  for field in grandchild:
                     if is_supplier_part_number(field):
                     #if is_manufacturer_part_number(field):
                        # Grab the part number and get out
                        part_number = field.text.strip()
                        break
                  # We now have at least the component reference, and hopefully
                  # the associated part number, get out.
                  break

            # Log the part number and component reference in the bom dictionary,
            # and show an error if no part number was found for this component.
            if part_number is not None:
               if not bom.has_key(part_number):
                  bom[part_number] = []

               bom[part_number].append(component_reference)
            else:
               sys.stderr.write("ERROR: Failed to find part number for %s!\n" % component_reference)
               retval = -1

         # This should never happen, but show a warning in case it does!
         if part_number is not None and component_reference is None:
            sys.stderr.write("WARNING: Found part number %s with no component reference!\n" % part_number)

# Print out Digikey style CSV BOM
for (part_number, components) in bom.iteritems():
   components.sort()
   out_file.write('%d,%s,%s\n' % (len(components), part_number, '|'.join(components)))
   component_count += len(components)

out_file.close()
print "BOM file of %d unique components (%d total) saved to: %s" % (len(bom), component_count, out_file_name)
sys.exit(retval)
