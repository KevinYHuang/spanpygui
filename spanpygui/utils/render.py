import cv2
import numpy as np

def render_segments(canvas, points, color=(0,0,255), thickness=2, alpha=1.0, output_alpha=False, marker='o', marker_size=5, marker_color=None):
    new_canvas = np.ones((canvas.shape[0], canvas.shape[1], 4 if output_alpha else 3), dtype=np.uint8)
    new_canvas[:,:,:3] = canvas
    # Convert rgb to bgr. Why does opencv use bgr
    if len(color) == 3 and not output_alpha: color = tuple(reversed(color))
    if marker_color is None: marker_color = color

    last_point = points[0].astype(int)
    if marker is not None:
        cv2.circle(new_canvas, last_point, radius=marker_size//2, color=marker_color, thickness=-1, lineType=cv2.LINE_AA)
    for point in points[1:]:
        cv2.line(new_canvas, last_point, point.astype(int), color=color, thickness=thickness, lineType=cv2.LINE_AA)
        last_point = point.astype(int)
        if marker is not None:
            cv2.circle(new_canvas, last_point, radius=marker_size//2, color=marker_color, thickness=-1, lineType=cv2.LINE_AA)

    if alpha < 1.0 and not output_alpha:
        new_canvas[:,:,:3] = cv2.addWeighted(canvas, 1 - alpha, new_canvas[:,:,:3], alpha, 0)
    if output_alpha:
        new_canvas[:,:,3] = alpha * (1 - new_canvas[:,:,3])

    return new_canvas

def render_image(canvas, image):
    # TODO maybe support non-stretching image setting
    canvas = cv2.resize(image, (canvas.shape[1], canvas.shape[0]), interpolation=cv2.INTER_NEAREST)
    return canvas

def render_weighted(canvas, image):
    return canvas * (1-image[:,:,3:]) + image[:,:,:3] * image[:,:,3:]