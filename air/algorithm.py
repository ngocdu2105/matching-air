import os
import sys
import time
import types
from six import PY3
from copy import deepcopy

from airtest import aircv
from airtest.aircv import cv2
# from airtest.core.helper import G, logwrap
# from airtest.core.settings import Settings as ST  # noqa
# from airtest.error import TargetNotFoundError, InvalidMatchingMethodError
from airtest.transform import TargetPos

from airtest.template_matching import TemplateMatching
from airtest.multiscale_template_matching import MultiScaleTemplateMatching,MultiScaleTemplateMatchingPre
from airtest.keypoint_matching import KAZEMatching, BRISKMatching, AKAZEMatching, ORBMatching
from airtest.keypoint_matching_contrib import SIFTMatching, SURFMatching, BRIEFMatching
from settings import Settings as ST


MATCHING_METHODS = {
    "tpl": TemplateMatching,
    "mstpl": MultiScaleTemplateMatchingPre,
    "gmstpl": MultiScaleTemplateMatching,
    "kaze": KAZEMatching,
    "brisk": BRISKMatching,
    "akaze": AKAZEMatching,
    "orb": ORBMatching,
    "sift": SIFTMatching,
    "surf": SURFMatching,
    "brief": BRIEFMatching,
}


class Template(object):
    """
    picture as touch/swipe/wait/exists target and extra info for cv match
    filename: pic filename
    target_pos: ret which pos in the pic
    record_pos: pos in screen when recording
    resolution: screen resolution when recording
    rgb: 识别结果是否使用rgb三通道进行校验.
    scale_max: 多尺度模板匹配最大范围.
    scale_step: 多尺度模板匹配搜索步长.
    """

    def __init__(self, filename, threshold=None, record_pos=None, resolution=(), rgb=False, scale_max=800, scale_step=0.005):
        self.filename = filename
        self._filepath = None
        self.threshold = threshold or ST.THRESHOLD
        self.target_pos = 0
        self.record_pos = record_pos
        self.resolution = resolution
        self.rgb = rgb
        self.scale_max = scale_max
        self.scale_step = scale_step

    # @property
    # def filepath(self):
    #     if self._filepath:
    #         return self._filepath
    #     for dirname in G.BASEDIR:
    #         filepath = os.path.join(dirname, self.filename)
    #         if os.path.isfile(filepath):
    #             self._filepath = filepath
    #             return self._filepath
    #     return self.filename

    def __repr__(self):
        filepath = self.filepath if PY3 else self.filepath.encode(sys.getfilesystemencoding())
        return "Template(%s)" % filepath

    def match_in(self, screen):
        """
        creen: đường dẫn creen dạng png, jpg
        """
        screen=aircv.imread(screen)
        image = aircv.imread(self.filename)
        match_result = self._cv_match(screen)
        # print("match result: %s", match_result)
        # aircv.mark_point(image,match_result['result'])
        # aircv.show(image)
        if not match_result:
            return None
        focus_pos = TargetPos().getXY(match_result, self.target_pos)        
        # aircv.mark_point(screen,match_result['location'][5])
        for point in match_result['rectangle']:
            aircv.mark_point(screen,point)
        aircv.show(screen)  # Thêm vào để show kết quả
        # print(focus_pos)
        return focus_pos

    def match_all_in(self, screen):
        """
        screen: đường dẫn png, jpg
        output: tất cả kết quả vị trí object có trong screen theo object
        """
        image = self._imread()
        screen = aircv.imread(screen)
        image = self._resize_image(image, screen, ST.RESIZE_METHOD)
        result = self._find_all_template(image, screen)
        for m in result:
            for point in m['rectangle']:
                aircv.mark_point(screen,point)
        aircv.show(screen)
        return [TargetPos().getXY(mr, self.target_pos) for mr in result] if result else None

    def _cv_match(self, screen):
        # in case image file not exist in current directory:
        ori_image = self._imread()
        image = self._resize_image(ori_image, screen, ST.RESIZE_METHOD)
        ret = None
        for method in ST.CVSTRATEGY:
            # get function definition and execute:
            func = MATCHING_METHODS.get(method, None)
            if func is None:
                raise Exception("Undefined method in CVSTRATEGY: '%s', try 'kaze'/'brisk'/'akaze'/'orb'/'surf'/'sift'/'brief' instead." % method)
            else:
                if method in ["mstpl", "gmstpl"]:
                    ret = self._try_match(func, ori_image, screen, threshold=self.threshold, rgb=self.rgb, record_pos=self.record_pos,
                                            resolution=self.resolution, scale_max=self.scale_max, scale_step=self.scale_step)
                else:
                    ret = self._try_match(func, image, screen, threshold=self.threshold, rgb=self.rgb)
            if ret:
                break
        return ret

    @staticmethod
    def _try_match(func, *args, **kwargs):
        print("try match with %s" % func.__name__)
        try:
            ret = func(*args, **kwargs).find_best_result()
        except aircv.NoModuleError as err:
            print("'surf'/'sift'/'brief' is in opencv-contrib module. You can use 'tpl'/'kaze'/'brisk'/'akaze'/'orb' in CVSTRATEGY, or reinstall opencv with the contrib module.")
            return None
        except aircv.BaseError as err:
            print(repr(err))
            return None
        # except:
        #     print('Erro suft, sift \n')
        # else:
        return ret

    def _imread(self):
        # print(self.filename)
        assert os.path.exists(self.filename),"No image_search in this path"
        return aircv.imread(self.filename)

    def _find_all_template(self, image, screen):
        return TemplateMatching(image, screen, threshold=self.threshold, rgb=self.rgb).find_all_results()

    def _find_keypoint_result_in_predict_area(self, func, image, screen):
        if not self.record_pos:
            return None
        # calc predict area in screen
        image_wh, screen_resolution = aircv.get_resolution(image), aircv.get_resolution(screen)
        xmin, ymin, xmax, ymax = Predictor.get_predict_area(self.record_pos, image_wh, self.resolution, screen_resolution)
        # crop predict image from screen
        predict_area = aircv.crop_image(screen, (xmin, ymin, xmax, ymax))
        if not predict_area.any():
            return None
        # keypoint matching in predicted area:
        ret_in_area = func(image, predict_area, threshold=self.threshold, rgb=self.rgb)
        # calc cv ret if found
        if not ret_in_area:
            return None
        ret = deepcopy(ret_in_area)
        if "rectangle" in ret:
            for idx, item in enumerate(ret["rectangle"]):
                ret["rectangle"][idx] = (item[0] + xmin, item[1] + ymin)
        ret["result"] = (ret_in_area["result"][0] + xmin, ret_in_area["result"][1] + ymin)
        return ret

    def _resize_image(self, image, screen, resize_method):
        """模板匹配中，将输入的截图适配成 等待模板匹配的截图."""
        # 未记录录制分辨率，跳过
        if not self.resolution:
            return image
        screen_resolution = aircv.get_resolution(screen)
        # 如果分辨率一致，则不需要进行im_search的适配:
        if tuple(self.resolution) == tuple(screen_resolution) or resize_method is None:
            return image
        if isinstance(resize_method, types.MethodType):
            resize_method = resize_method.__func__
        # 分辨率不一致则进行适配，默认使用cocos_min_strategy:
        h, w = image.shape[:2]
        w_re, h_re = resize_method(w, h, self.resolution, screen_resolution)
        # 确保w_re和h_re > 0, 至少有1个像素:
        w_re, h_re = max(1, w_re), max(1, h_re)
        # 调试代码: 输出调试信息.
        print("resize: (%s, %s)->(%s, %s), resolution: %s=>%s" % (
                        w, h, w_re, h_re, self.resolution, screen_resolution))
        # 进行图片缩放:
        image = cv2.resize(image, (w_re, h_re))
        return image


class Predictor(object):
    """
    this class predicts the press_point and the area to search im_search.
    """

    DEVIATION = 100

    @staticmethod
    def count_record_pos(pos, resolution):
        """计算坐标对应的中点偏移值相对于分辨率的百分比."""
        _w, _h = resolution
        # 都按宽度缩放，针对G18的实验结论
        delta_x = (pos[0] - _w * 0.5) / _w
        delta_y = (pos[1] - _h * 0.5) / _w
        delta_x = round(delta_x, 3)
        delta_y = round(delta_y, 3)
        return delta_x, delta_y

    @classmethod
    def get_predict_point(cls, record_pos, screen_resolution):
        """预测缩放后的点击位置点."""
        delta_x, delta_y = record_pos
        _w, _h = screen_resolution
        target_x = delta_x * _w + _w * 0.5
        target_y = delta_y * _w + _h * 0.5
        return target_x, target_y

    @classmethod
    def get_predict_area(cls, record_pos, image_wh, image_resolution=(), screen_resolution=()):
        """Get predicted area in screen."""
        x, y = cls.get_predict_point(record_pos, screen_resolution)
        # The prediction area should depend on the image size:
        if image_resolution:
            predict_x_radius = int(image_wh[0] * screen_resolution[0] / (2 * image_resolution[0])) + cls.DEVIATION
            predict_y_radius = int(image_wh[1] * screen_resolution[1] / (2 * image_resolution[1])) + cls.DEVIATION
        else:
            predict_x_radius, predict_y_radius = int(image_wh[0] / 2) + cls.DEVIATION, int(image_wh[1] / 2) + cls.DEVIATION
        area = (x - predict_x_radius, y - predict_y_radius, x + predict_x_radius, y + predict_y_radius)
        return area


