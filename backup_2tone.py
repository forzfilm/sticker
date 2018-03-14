# -*- coding: utf-8 -*-
"""
Created on Mon Mar 20 12:28:21 2017
@author: Hriddhi Dey
This module contains the ApplyMakeup class.
"""

import itertools
import scipy.interpolate
import cv2
import numpy as np
from skimage import color
from  visage.detect_features import DetectLandmarks
import os
from shapely.geometry import Polygon

class ApplyMakeup(DetectLandmarks):
    """
    Class that handles application of color, and performs blending on image.
    Functions available for use:
        1. apply_lipstick: Applies lipstick on passed image of face.
        2. apply_liner: Applies black eyeliner on passed image of face.
    """

    def __init__(self):
        """ Initiator method for class """
        DetectLandmarks.__init__(self)
        self.red_l = 0
        self.green_l = 0
        self.blue_l = 0
        self.red_e = 0
        self.green_e = 0
        self.blue_e = 0
        self.debug = 0
        self.image = 0
        self.width = 0
        self.height = 0
        self.im_copy = 0
        self.lip_x = []
        self.lip_y = []


    def __read_image(self, filename):
        """ Read image from path forwarded """
        self.image = cv2.imread(filename)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.im_copy = self.image.copy()
        self.height, self.width = self.image.shape[:2]
        self.debug = 0


    def __draw_curve(self, points):
        """ Draws a curve alone the given points by creating an interpolated path. """
        x_pts = []
        y_pts = []
        curvex = []
        curvey = []
        self.debug += 1
        for point in points:
            x_pts.append(point[0])
            y_pts.append(point[1])
        curve = scipy.interpolate.interp1d(x_pts, y_pts, 'cubic')
        if self.debug == 1 or self.debug == 2:
            for i in np.arange(x_pts[0], x_pts[len(x_pts) - 1] + 1, 1):
                curvex.append(i)
                curvey.append(int(curve(i)))
        else:
            for i in np.arange(x_pts[len(x_pts) - 1] + 1, x_pts[0], 1):
                curvex.append(i)
                curvey.append(int(curve(i)))
        return curvex, curvey


    def __fill_lip_lines(self, outer, inner):
        """ Fills the outlines of a lip with colour. """
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        count = len(inner[0]) - 1
        last_inner = [inner[0][count], inner[1][count]]
        for o_point, i_point in itertools.zip_longest(
                outer_curve, inner_curve, fillvalue=last_inner
            ):
            line = scipy.interpolate.interp1d(
                [o_point[0], i_point[0]], [o_point[1], i_point[1]], 'linear')
            xpoints = list(np.arange(o_point[0], i_point[0], 1))
            self.lip_x.extend(xpoints)
            self.lip_y.extend([int(point) for point in line(xpoints)])
        return

    def hex_to_RGB(self,hex):
      ''' "#FFFFFF" -> [255,255,255] '''
      # Pass 16 to the integer function for change of base
      return [int(hex[i:i+2], 16) for i in range(1,6,2)]

    def RGB_to_hex(self,RGB):
      ''' [255,255,255] -> "#FFFFFF" '''
      # Components need to be integers for hex to make sense
      RGB = [int(x) for x in RGB]
      return "#"+"".join(["0{0:x}".format(v) if v < 16 else
                "{0:x}".format(v) for v in RGB])

    def color_dict(self,gradient):
      ''' Takes in a list of RGB sub-lists and returns dictionary of
        colors in RGB and hex form for use in a graphing function
        defined later on '''
      return {"hex":[self.RGB_to_hex(RGB) for RGB in gradient],
          "r":[RGB[0] for RGB in gradient],
          "g":[RGB[1] for RGB in gradient],
          "b":[RGB[2] for RGB in gradient]}


    def linear_gradient(self,start_hex, finish_hex, n):
      ''' returns a gradient list of (n) colors between
        two hex colors. start_hex and finish_hex
        should be the full six-digit color string,
        inlcuding the number sign ("#FFFFFF") '''
      # Starting and ending colors in RGB form
      s = self.hex_to_RGB(start_hex)
      f = self.hex_to_RGB(finish_hex)
      # Initilize a list of the output colors with the starting color
      RGB_list = [s]
      # Calcuate a color at each evenly spaced value of t from 1 to n
      for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
          int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
          for j in range(3)
        ]
        # Add it to our list of output colors
        RGB_list.append(curr_vector)

      return self.color_dict(RGB_list)

    def __fill_lip_solid(self, outer, inner,min_inner_color,max_inner_color,min_outer_color,max_outer_color):
        """ Fills solid colour inside two outlines. """
        print("outer %s", outer)
        print("inner %s", inner)
        inner[0].reverse()
        inner[1].reverse()
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        outer_count = zip(outer[0], outer[1])
        inner_count = zip(inner[0], inner[1])
        len_outer = sum(1 for _ in outer_count)
        len_inner = sum(1 for _ in inner_count)
        gradient_outer = self.linear_gradient(min_inner_color,max_inner_color,len_outer)
        gradient_inner = self.linear_gradient(min_outer_color,max_outer_color,len_inner)
        i = 0
        points = []
        for point in outer_curve:
            if i <= len_outer/2:
                points.append(np.array(point, dtype=np.int32))
                color_red = gradient_outer["r"]
                color_green = gradient_outer["g"]
                color_blue = gradient_outer["b"]
                points_np = np.array(points, dtype=np.int32)
                cv2.fillPoly(self.image, [points_np], (color_red[i],color_green[i],color_blue[i]))
            else:
                if i == (len_outer/2)+1:
                    points = [points[-1]]
                points.append(np.array(point, dtype=np.int32))
                color_red = gradient_outer["r"]
                color_green = gradient_outer["g"]
                color_blue = gradient_outer["b"]
                points_np = np.array(points, dtype=np.int32)
                cv2.fillPoly(self.image, [points_np], (color_red[i],color_green[i],color_blue[i]))
            i += 1

        i = 0
        for point in inner_curve:
            if i <= len_inner/2:
                points.append(np.array(point, dtype=np.int32))
                color_red = gradient_inner["r"]
                color_green = gradient_inner["g"]
                color_blue = gradient_inner["b"]
                points_np = np.array(points, dtype=np.int32)
                cv2.fillPoly(self.image, [points_np], (color_red[i],color_green[i],color_blue[i]))
            else:
                if i == (len_inner/2)+1:
                    points = [points[-1]]
                points.append(np.array(point, dtype=np.int32))
                color_red = gradient_inner["r"]
                color_green = gradient_inner["g"]
                color_blue = gradient_inner["b"]
                points_np = np.array(points, dtype=np.int32)
                cv2.fillPoly(self.image, [points_np], (color_red[i],color_green[i],color_blue[i]))
                points_np = np.array(points, dtype=np.int32)
                cv2.fillPoly(self.image, [points_np], (color_red[i],color_green[i],color_blue[i]))
            i += 1
        # points = np.array(points, dtype=np.int32)
        # print(points)
        # self.red_l = int(self.red_l)
        # self.green_l = int(self.green_l)
        # self.blue_l = int(self.blue_l)
        # cv2.fillPoly(self.image, [points], (self.red_l, self.green_l, self.blue_l))


    def __smoothen_color(self, outer, inner):
        """ Smoothens and blends colour applied between a set of outlines. """
        outer_curve = zip(outer[0], outer[1])
        inner_curve = zip(inner[0], inner[1])
        x_points = []
        y_points = []
        for point in outer_curve:
            x_points.append(point[0])
            y_points.append(point[1])
        for point in inner_curve:
            x_points.append(point[0])
            y_points.append(point[1])
        img_base = np.zeros((self.height, self.width))
        cv2.fillConvexPoly(img_base, np.array(np.c_[x_points, y_points], dtype='int32'), 1)
        img_mask = cv2.GaussianBlur(img_base, (51, 51), 0)
        img_blur_3d = np.ndarray([self.height, self.width, 3], dtype='float')
        img_blur_3d[:, :, 0] = img_mask
        img_blur_3d[:, :, 1] = img_mask
        img_blur_3d[:, :, 2] = img_mask
        self.im_copy = (img_blur_3d * self.image + (1 - img_blur_3d) * self.im_copy).astype('uint8')


    def __draw_liner(self, eye, kind):
        """ Draws eyeliner. """
        eye_x = []
        eye_y = []
        x_points = []
        y_points = []
        for point in eye:
            x_points.append(int(point.split()[0]))
            y_points.append(int(point.split()[1]))
        curve = scipy.interpolate.interp1d(x_points, y_points, 'quadratic')
        for point in np.arange(x_points[0], x_points[len(x_points) - 1] + 1, 1):
            eye_x.append(point)
            eye_y.append(int(curve(point)))
        if kind == 'left':
            y_points[0] -= 1
            y_points[1] -= 1
            y_points[2] -= 1
            x_points[0] -= 5
            x_points[1] -= 1
            x_points[2] -= 1
            curve = scipy.interpolate.interp1d(x_points, y_points, 'quadratic')
            count = 0
            for point in np.arange(x_points[len(x_points) - 1], x_points[0], -1):
                count += 1
                eye_x.append(point)
                if count < (len(x_points) / 2):
                    eye_y.append(int(curve(point)))
                elif count < (2 * len(x_points) / 3):
                    eye_y.append(int(curve(point)) - 1)
                elif count < (4 * len(x_points) / 5):
                    eye_y.append(int(curve(point)) - 2)
                else:
                    eye_y.append(int(curve(point)) - 3)
        elif kind == 'right':
            x_points[3] += 5
            x_points[2] += 1
            x_points[1] += 1
            y_points[3] -= 1
            y_points[2] -= 1
            y_points[1] -= 1
            curve = scipy.interpolate.interp1d(x_points, y_points, 'quadratic')
            count = 0
            for point in np.arange(x_points[len(x_points) - 1], x_points[0], -1):
                count += 1
                eye_x.append(point)
                if count < (len(x_points) / 2):
                    eye_y.append(int(curve(point)))
                elif count < (2 * len(x_points) / 3):
                    eye_y.append(int(curve(point)) - 1)
                elif count < (4 * len(x_points) / 5):
                    eye_y.append(int(curve(point)) - 2)
                elif count:
                    eye_y.append(int(curve(point)) - 3)
        curve = zip(eye_x, eye_y)
        points = []
        for point in curve:
            points.append(np.array(point, dtype=np.int32))
        points = np.array(points, dtype=np.int32)
        self.red_e = int(self.red_e)
        self.green_e = int(self.green_e)
        self.blue_e = int(self.blue_e)
        cv2.fillPoly(self.im_copy, [points], (self.red_e, self.green_e, self.blue_e))
        return


    def __add_color(self, intensity):
        """ Adds base colour to all points on lips, at mentioned intensity. """
        val = color.rgb2lab(
            (self.image[self.lip_y, self.lip_x] / 255.)
            .reshape(len(self.lip_y), 1, 3)
        ).reshape(len(self.lip_y), 3)
        l_val, a_val, b_val = np.mean(val[:, 0]), np.mean(val[:, 1]), np.mean(val[:, 2])
        l1_val, a1_val, b1_val = color.rgb2lab(
            np.array(
                (self.red_l / 255., self.green_l / 255., self.blue_l / 255.)
                ).reshape(1, 1, 3)
            ).reshape(3,)
        l_final, a_final, b_final = (l1_val - l_val) * \
            intensity, (a1_val - a_val) * \
            intensity, (b1_val - b_val) * intensity
        val[:, 0] = np.clip(val[:, 0] + l_final, 0, 100)
        val[:, 1] = np.clip(val[:, 1] + a_final, -127, 128)
        val[:, 2] = np.clip(val[:, 2] + b_final, -127, 128)
        self.image[self.lip_y, self.lip_x] = color.lab2rgb(val.reshape(
            len(self.lip_y), 1, 3)).reshape(len(self.lip_y), 3) * 255


    def __get_points_lips(self, lips_points):
        """ Get the points for the lips. """
        uol = []
        uil = []
        lol = []
        lil = []
        for i in range(0, 14, 2):
            uol.append([int(lips_points[i]), int(lips_points[i + 1])])
        for i in range(12, 24, 2):
            lol.append([int(lips_points[i]), int(lips_points[i + 1])])
        lol.append([int(lips_points[0]), int(lips_points[1])])
        for i in range(24, 34, 2):
            uil.append([int(lips_points[i]), int(lips_points[i + 1])])
        for i in range(32, 40, 2):
            lil.append([int(lips_points[i]), int(lips_points[i + 1])])
        lil.append([int(lips_points[24]), int(lips_points[25])])
        return uol, uil, lol, lil


    def __get_curves_lips(self, uol, uil, lol, lil):
        """ Get the outlines of the lips. """
        uol_curve = self.__draw_curve(uol)
        uil_curve = self.__draw_curve(uil)
        lol_curve = self.__draw_curve(lol)
        lil_curve = self.__draw_curve(lil)
        return uol_curve, uil_curve, lol_curve, lil_curve


    def __fill_color(self, uol_c, uil_c, lol_c, lil_c,min_inner_color,max_inner_color,min_outer_color,max_outer_color):
        """ Fill colour in lips. """
        self.__fill_lip_lines(uol_c, uil_c)
        self.__fill_lip_lines(lol_c, lil_c)
        self.__add_color(0.5)
        self.__fill_lip_solid(uol_c, uil_c, min_inner_color,max_inner_color,min_outer_color,max_outer_color)
        self.__fill_lip_solid(lol_c, lil_c, min_inner_color,max_inner_color,min_outer_color,max_outer_color)
        self.__smoothen_color(uol_c, uil_c)
        self.__smoothen_color(lol_c, lil_c)

        self.__add_color(0.3)

    def __fill_color_bottom(self, uol_c, uil_c, lol_c, lil_c,min_inner_color,max_inner_color,min_outer_color,max_outer_color):
        """ Fill colour in lips. """
        self.__fill_lip_lines(uol_c, uil_c)
        self.__fill_lip_lines(lol_c, lil_c)
        self.__add_color(0.5)
        # self.__fill_lip_solid(uol_c, uil_c)
        self.__fill_lip_solid(lol_c, lil_c,min_inner_color,max_inner_color,min_outer_color,max_outer_color)
        # self.__smoothen_color(uol_c, uil_c)
        self.__smoothen_color(lol_c, lil_c)

        self.__add_color(0.3)

    def __fill_color_upper(self, uol_c, uil_c, lol_c, lil_c,min_inner_color,max_inner_color,min_outer_color,max_outer_color):
        """ Fill colour in lips. """
        self.__fill_lip_lines(uol_c, uil_c)
        self.__fill_lip_lines(lol_c, lil_c)
        self.__add_color(0.5)
        self.__fill_lip_solid(uol_c, uil_c,min_inner_color,max_inner_color,min_outer_color,max_outer_color)
        # self.__fill_lip_solid(lol_c, lil_c)
        self.__smoothen_color(uol_c, uil_c)
        # self.__smoothen_color(lol_c, lil_c)

        self.__add_color(0.3)

    def __create_eye_liner(self, eyes_points):
        """ Apply eyeliner. """
        left_eye = eyes_points[0].split('\n')
        right_eye = eyes_points[1].split('\n')
        right_eye = right_eye[0:4]
        self.__draw_liner(left_eye, 'left')
        self.__draw_liner(right_eye, 'right')


    def apply_lipstick(self, filename, rlips, glips, blips,position):
        """
        Applies lipstick on an input image.
        ___________________________________
        Args:
            1. `filename (str)`: Path for stored input image file.
            2. `red (int)`: Red value of RGB colour code of lipstick shade.
            3. `blue (int)`: Blue value of RGB colour code of lipstick shade.
            4. `green (int)`: Green value of RGB colour code of lipstick shade.
        Returns:
            `filepath (str)` of the saved output file, with applied lipstick.
        """

        self.red_l = rlips
        self.green_l = glips
        self.blue_l = blips
        self.__read_image(filename)
        lips = self.get_lips(self.image)
        lips = list([point.split() for point in lips.split('\n')])
        lips_points = [item for sublist in lips for item in sublist]
        uol, uil, lol, lil = self.__get_points_lips(lips_points)
        uol_c, uil_c, lol_c, lil_c = self.__get_curves_lips(uol, uil, lol, lil)
        if position == "upper":
            self.__fill_color_upper(uol_c, uil_c, lol_c, lil_c,"#6D0000","#FF0000","#FF00F4","#F6B9F4")
        elif position == "bottom":
            self.__fill_color_bottom(uol_c, uil_c, lol_c, lil_c,"#2119fd","#2119fd","#000000","#000000")
        else:
            self.__fill_color(uol_c, uil_c, lol_c, lil_c)

        self.im_copy = cv2.cvtColor(self.im_copy, cv2.COLOR_BGR2RGB)
        name = 'color_' + str(self.red_l) + '_' + str(self.green_l) + '_' + str(self.blue_l)
        path, filename = os.path.split(filename)
        file_name = 'output_lips_' + filename
        cv2.imwrite(file_name, self.im_copy)
        return file_name


    def apply_liner(self, filename):
        """
        Applies lipstick on an input image.
        ___________________________________
        Args:
            1. `filename (str)`: Path for stored input image file.
        Returns:
            `filepath (str)` of the saved output file, with applied lipstick.
        """
        self.__read_image(filename)
        liner = self.get_upper_eyelids(self.image)
        eyes_points = liner.split('\n\n')
        self.__create_eye_liner(eyes_points)
        self.im_copy = cv2.cvtColor(self.im_copy, cv2.COLOR_BGR2RGB)
        name = '_color_' + str(self.red_l) + '_' + str(self.green_l) + '_' + str(self.blue_l)
        path, filename = os.path.split(path/to/file/foobar.txt)
        file_name = 'output_eyeliner_' + filename
        cv2.imwrite(file_name, self.im_copy)
        return file_name
