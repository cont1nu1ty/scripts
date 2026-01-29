# scripts
无用脚本
sort_playlist:
    将lxmusic导出的list按照指定txt文件排序，重新打包为数据文件
    lx_list.lxmc (压缩文件)
        ↓ [1] 解压
    lx_list (JSON文件)
        ↓ [2] 读取歌曲列表 (121.txt)
        ↓ [3] 读取歌单数据
        ↓ [4] 查找并排序歌单
    lx_list (排序后的JSON)
        ↓ [5] 保存
        ↓ [6] 压缩
    lx_list.lxmc (新的压缩文件)
        ↓ 清理临时文件