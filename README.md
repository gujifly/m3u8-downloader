# m3u8-downloader
download tools for m3u8  media

功能：
   目前（2019年）很多在线视频网站都使用 m3u8 方式播放视频，m3u8 文件是一个索引文件，
   网页播放器解析m3u8 来下载 ts 文件播放。由于 ts 文件体积小、数量大，逐个下载不方便，于是产生编写下载脚本的想法。

特点：
0. 根据 m3u8 文件，自动下载所有 ts 文件，最后合并成一个 ts 文件
1. 支持多线程下载（默认设置线程池数：32 ）
2. 支持断点续传（其实就是重复执行时，跳过已下载的文件）
3. 支持进度条显示（让下载过程有个盼头 ...）
4. 支持加密类型(AES-128) 的 m3u8文件
5. 支持嵌套类型（两层）的 m3u8 文件

脚本参考了以下两位仁兄的代码（在此表示感谢）：
https://blog.csdn.net/lswzw/article/details/101067803
https://blog.csdn.net/a33445621/article/details/80377424

环境：
    CentOS 7.6 x 64
    Python3.6.4
    
安装必备库：
pip3  install  requests  progressbar  pycrypto

使用方式：
python3   m3u8_downloader.py   https://xxxxx/xxx/index.m3u8    moviename

其中  https://xxxxx/xxx/index.m3u8 为 m3u8 文件url
      moviename  为合并后的文件名（自定义）
      
示例：
python3  m3u8_downloader.py   https://xxxxx/xxx/index.m3u8    zhizhuxia
python3  m3u8_downloader.py   https://xxxxx/xxx/index.m3u8    mymovie

      
注意事项：
0. 下载的文件，默认存放在当前 ./bak/ 目录下，下载-合并完成后，该目录不会被删除（重新执行脚本时，避免重复下载）
   所以，如果下载完一步电影后，请自己清空 ./bak/ 目录哈（ rm -f ./bak/* ）

1. 下载完毕后，会自动进行文件合并，注意 fail_list 提示。
   1.1 如果 fail_list 一栏为空，则表示所有 ts 均下载完毕，合并的文件是完整的。
   1.2 如果 fail_list 一栏不为空（由于网络原因，部分文件下载失败），则重新运行一次脚本即可（已下载的文件会跳过，不会重复下载）

2. 没有针对大量的链接测试，如果有 bug ，请自己尝试修复哈。

