# _*_ coding:UTF-8 _*_


class TargetPos(object):
    """
    点击目标图片的不同位置，默认为中心点0
    1 2 3
    4 0 6
    7 8 9
    """
    LEFTUP, UP, RIGHTUP = 1, 2, 3
    LEFT, MID, RIGHT = 4, 5, 6
    LEFTDOWN, DOWN, RIGHTDOWN = 7, 8, 9

    def getXY(self, cvret, pos):
        if not cvret:
            return None
        rect = cvret.get("rectangle")
        if not rect:
            print("could not get rectangle, use mid point instead")
            return cvret["result"]
        w = rect[2][0] - rect[0][0]
        h = rect[2][1] - rect[0][1]
        leftup=rect[0]

        leftdown=rect[1]

        rightdown=rect[2]

        rightup=rect[3]

        left= (rect[0][0], rect[0][1] + h / 2)

        up= (rect[0][0] + w / 2, rect[0][1])

        right= (rect[2][0], rect[2][1] - h / 2)

        down=(rect[2][0] - w / 2, rect[2][1])

        cvret["location"]= {
            self.LEFTUP:leftup,
            self.UP:up,
            self.RIGHTUP:rightup,
            self.LEFT:left,
            self.MID:cvret["result"],
            self.RIGHT:right,
            self.LEFTDOWN:leftdown,
            self.DOWN:down, 
            self.RIGHTDOWN:rightdown,
        }
        return cvret
