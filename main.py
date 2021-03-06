import numpy as np
import sys
import tensorflow as tf
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
import cv2

from interpolator import Grid
from obstacle import Obstacle
from robot import Robot

#-------------------------------------------------------------------------------
# Configuration
#-------------------------------------------------------------------------------

# flag to turn visualization on/off
SHOW_VISUALIZATION = True

# minimum acceptable detection score (to be detected as obstacle)
MINIMUM_DETECTION_SCORE = 0.90

# Path to frozen detection graph. This is the actual model that is used for the object detection.
PATH_TO_FROZEN_GRAPH = '/home/pi/ssd_mobilenet_trained_model/frozen_inference_graph.pb'

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = '/home/pi/ssd_mobilenet_trained_model/label_map.pbtxt'

# Path to the file containing the calibration grid
PATH_TO_CALIBRATION_GRID = 'calibration_grid.yaml'

#-------------------------------------------------------------------------------
# Initialization
#-------------------------------------------------------------------------------

print("Opening Detection Graph")

# Load frozen Tensorflow model into memory
detection_graph = tf.Graph()
with detection_graph.as_default():
  od_graph_def = tf.GraphDef()
  with tf.gfile.GFile(PATH_TO_FROZEN_GRAPH, 'rb') as fid:
    serialized_graph = fid.read()
    od_graph_def.ParseFromString(serialized_graph)
    tf.import_graph_def(od_graph_def, name='')

# Load label map
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

#-------------------------------------------------------------------------------
# Helper Code
#-------------------------------------------------------------------------------

def run_inference_for_single_image(image, graph, sess):
  # Get handles to input and output tensors
  ops = tf.get_default_graph().get_operations()
  all_tensor_names = {output.name for op in ops for output in op.outputs}
  tensor_dict = {}
  for key in [
      'num_detections', 'detection_boxes', 'detection_scores',
      'detection_classes', 'detection_masks'
  ]:
    tensor_name = key + ':0'
    if tensor_name in all_tensor_names:
      tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
          tensor_name)
  if 'detection_masks' in tensor_dict:
    # The following processing is only for single image
    detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
    detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
    # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
    real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
    detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
    detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
    detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
        detection_masks, detection_boxes, image.shape[0], image.shape[1])
    detection_masks_reframed = tf.cast(
        tf.greater(detection_masks_reframed, 0.5), tf.uint8)
    # Follow the convention by adding back the batch dimension
    tensor_dict['detection_masks'] = tf.expand_dims(
        detection_masks_reframed, 0)
  image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

  # Run inference
  output_dict = sess.run(tensor_dict, feed_dict={image_tensor: np.expand_dims(image, 0)})

  # all outputs are float32 numpy arrays, so convert types as appropriate
  output_dict['num_detections'] = int(output_dict['num_detections'][0])
  output_dict['detection_classes'] = output_dict['detection_classes'][0].astype(np.uint8)
  output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
  output_dict['detection_scores'] = output_dict['detection_scores'][0]
  if 'detection_masks' in output_dict:
      output_dict['detection_masks'] = output_dict['detection_masks'][0]
  return output_dict

#-------------------------------------------------------------------------------
# Main Script
#-------------------------------------------------------------------------------

if __name__ == '__main__':
  # camera object
  capture = cv2.VideoCapture(0)

  # communications
  audree = Robot.Robot()

  # calibration grid
  grid = Grid.Grid(PATH_TO_CALIBRATION_GRID)

  # start detecting obstacles
  with detection_graph.as_default():
    with tf.Session() as sess:
      while True:

        # break if camera failure
        if not capture.isOpened():
          print("Could not open camera")
          break

        # flush the camera buffer
        for i in range(5):
          capture.grab()

        # get latest frame
        ret, image_np = capture.retrieve()

        # Actual detection.
        output_dict = run_inference_for_single_image(image_np, detection_graph, sess)
        count = 0

        # send data to AUDREE
        print(80 * '-')
        for i in range(output_dict['num_detections']):
            if output_dict['detection_scores'][i] >= MINIMUM_DETECTION_SCORE:

                # get pixel col and row of center of obstacles
                [row_min, col_min, row_max, col_max] = output_dict['detection_boxes'][i]
                col = int(np.mean([col_min, col_max]) * image_np.shape[1])
                row = int(np.mean([row_min, row_max]) * image_np.shape[0])

                # convert col/row to x/y
                (x, y) = grid.interpolate(col, row)
                print('x - ', x)
                print('y - ', y)

                # push to buffer
                audree.add_obstacle(Obstacle.Obstacle(x, y))

                count += 1
            else:
                break

        # visualize
        if SHOW_VISUALIZATION:
            vis_util.visualize_boxes_and_labels_on_image_array(
                image_np,
                output_dict['detection_boxes'],
                output_dict['detection_classes'],
                output_dict['detection_scores'],
                category_index,
                instance_masks = output_dict.get('detection_masks'),
                use_normalized_coordinates = True,
                line_thickness = 5,
                min_score_thresh = MINIMUM_DETECTION_SCORE
                )
            cv2.imshow('Live Feed', cv2.resize(image_np, (800, 600)))
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break

        print("Num obstacles: ", count)
        audree.send_obstacles()
        
