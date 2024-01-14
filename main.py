from pathlib import Path
from paquo.projects import QuPathProject
import shapely
import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
import os

OPENSLIDE_PATH = r'C:\Users\flori\Documents\UNI_2017-in_corso\Biennale\primo_anno\II_semestre\SDTRA\progettoSDTRA\openslide-win64-20220811\bin'
if hasattr(os, 'add_dll_directory'):
    #Python >= 3.8 on Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
        from openslide import OpenSlide


def read_qupath_annotations(image):
    """Read annotations from QuPath image, return list"""
    annotations = image.hierarchy.annotations  # annotations are accessible via the hierarchy
    #print(f"Image {image.image_name} has {len(annotations)} annotations.")
    ann = [annotation.roi for annotation in annotations] if annotations else list()  # Return empty list if annotations are missing
    return ann, annotations


def check_boundaries(x, y, size):
    x_min = 0
    x_max = size
    y_min = 0
    y_max = size

    isin = False
    for i in range(len(x)):
        if round(x[i]) in range(x_min, x_max) and round(y[i]) \
                in range(y_min, y_max):
            isin = True
            break
    return isin


def add_annotations_image(annotations, ann, downsample_fact, size, entry, j):
    num = len(ann)
    centroid_xy_cent = ann[j].centroid.bounds[0:2]
    for k in range(num):
        class_ann = str(annotations[k].path_class).replace('QuPathPathClass', '')
        if class_ann == "('Glomerulus')":
            offset_x = centroid_xy_cent[0] - (size // 2) * downsample_fact
            offset_y = centroid_xy_cent[1] - (size // 2) * downsample_fact
            new_ann = shapely.affinity.translate(ann[k], xoff=-offset_x, yoff=-offset_y)

            new_ann = shapely.affinity.scale(new_ann, xfact=1 / downsample_fact, yfact=1 / downsample_fact,
                                             origin=(0, 0))

            if str(type(new_ann.boundary)) == "<class 'shapely.geometry.multilinestring.MultiLineString'>":
                coords_x = new_ann.boundary[0].coords.xy[0]
                coords_y = new_ann.boundary[0].coords.xy[1]
                isin = check_boundaries(coords_x, coords_y, size)
            else:
                coords_x = new_ann.boundary.coords.xy[0]
                coords_y = new_ann.boundary.coords.xy[1]
                isin = check_boundaries(coords_x, coords_y, size)

            if isin == True:
                entry.hierarchy.add_annotation(roi=new_ann)
                print(f"The number {k} annotation was added")


def add_image_new_project(image, ann, annotations, qpout, ops, downsample_fact, size, i, j, data_path):
    level = ops.get_best_level_for_downsample(downsample_fact)
    id = f"_____{str(i + 1)}_{str(j + 1)}"
    #path_glom = data_path + f"/new/PanGNBariCropped_train/{image.image_name.replace('.ndpi', '')}_" + id + ".jpeg"
    path_glom = data_path + f"/test/{image.image_name.replace('.ndpi', '')}_" + id + ".jpeg"
    class_ann = str(annotations[j].path_class).replace('QuPathPathClass', '')
    if class_ann == "('Glomerulus')":
        print("It's a glomerulus ;)")
        if not os.path.isfile(path_glom):
            location = ann[j].centroid.bounds[0:2]
            x = int(location[0] - (size // 2) * downsample_fact)
            y = int(location[1] - (size // 2) * downsample_fact)

            osh = ops.read_region(location=(x, y), level=level, size=(size, size))

            osh = osh.convert('RGB')
            osh.save(path_glom)
            print(f"Image {str(j + 1)}/{len(ann)} saved\n")
        entry = qpout.add_image(path_glom, image.image_type, allow_duplicates=False)
        add_annotations_image(annotations, ann, downsample_fact, size, entry, j)

        # else:
        #    print('It is not a glomerulus :(')


def main():
    PROJECT_NAME = "PanGNBariSegmentationR2"
    data_path = "E:/Segmentazione Glomeruli"
    PROJECT_PATH = f"{data_path}/Nuova Cartella/{PROJECT_NAME}/project.qpproj"
    NEW_PROJECT_PATH = f"{data_path}/test/{PROJECT_NAME}_out_test/project.qpproj"
    downsample_fact = 4
    size = 1000

    with QuPathProject(NEW_PROJECT_PATH, mode='a') as qpout:
        qp = QuPathProject(PROJECT_PATH, mode='r')
        print(f"Opened project ‘{qp.name}’ ")
        print(f"Created new QuPath project: '{qpout.name}'.")
        print(f"Project has {len(qp.images)} image(s).")
        images = qp.images
        num_images = len(qp.images)
        num_images = 1
        for i in range(num_images):

            image = images[i]
            wsi_fname = image.uri.replace("file:///", '').replace("%20", ' ')
            with openslide.OpenSlide(wsi_fname) as ops:
                ann, annotations = read_qupath_annotations(image)
                num_ann = len(annotations)
                # print(f"number of ann {num_ann}")
                for j in range(2):
                    add_image_new_project(image, ann, annotations, qpout, ops, downsample_fact, size, i - 1, j,
                                          data_path)

main()