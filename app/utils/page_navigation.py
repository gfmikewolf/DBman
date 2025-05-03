# utils/navigation.py
# 获取本层的导航字典：默认为首页到crud页，可选参数为后续添加的导航项
# 本层的默认导航字典需要设置全局变量_navigation
class PageNavigation:
    index : dict[str, str] = {}

    def __init__(self, index : dict[str, str]):
        self.index = index

    def get_nav(self, nav : dict[str, str]) -> dict[str, str]:
        # 如果定义了本视图的基础字典，使用基础字典，否则使用默认字典
        if self.index:
            updated = self.index.copy()
        else:
            updated = {}
        # 更新参数中的字典到视图的基础字典
        for key in nav:
            updated[key] = nav[key]
        return updated
