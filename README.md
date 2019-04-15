# stroller-spotter
Pedestrian annotation tool for CNN based crowd counting

# Description

This is an annotation tool for creating head annotations in MATLAB *.mat file format for CNN based crowd counting solutions. The tool is still very plain but almightiness was not in our agenda. We just wanted an open source annotation tool that is more convenient than the existing MATLAB script. At the moment it is only alpha tested, still contains bugs. The tool can only be used to annotate *.jpg, *.png and *.gif images. If the file types are not matching the extensions then the behavior is undefined.

# Usage

The GUI was designed to somewhat resemble that of the LabelImg tool. Although it is much simpler.

Clicking the "Open folder" button will bring up a dialog where the user may browse to a directory from where images should be loaded. After doing so, all *.jpg, *.png and *.gif images will be loaded to the images list on the right. The opening action will automatically set the save directory to the "mat_files" folder inside the image folder if it exists. Otherwise it will not be set, and will have to be set before saving. If the directory exists, upon opening the image directory any matching annotations present will automatically be loaded. Matching annotation means that the annotation file name is the same as the image file name except for the extensions which ".mat" for the annotation file. In case there are pending changes in the current work a dialog will pop up asking if the user wants to proceed, if so all pending changes will be lost.

Clicking the "Set save directory" button  will bring up a dialog where the user may browse to a directory to where the output files should saved. If there are any matching annotation files in the selected directory their contents will be loaded.

Clicking the "Save" button will save the current annotation in the selected save directory. If there is no save directory set yet a "Set save directory" dialog will pop up first.

Clicking the "Add points mode" button will allow the user to add new annotations to an image if it is selected. Every pixel can be annotated, however one pixel can be annotated only once.

Clicking the "Select points mode" button will allow the user to select and deselect annotated points. Selected points are red, deselected points are red. The selection has a 6 pixel long radius but it always selects the nearest point. Pressing the delete button on the keyboard will delete the selected annotations.
