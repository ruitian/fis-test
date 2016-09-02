fis.config.merge({
    namespace : 'home',
    pack : {
        'static/pkg/aio.css' : [
            'static/lib/css/bootstrap.css',
            'static/lib/css/bootstrap-responsive.css',
            'widget/**.css'
        ],
        'static/pkg/aio.js' : [
            'static/lib/js/jquery-1.10.1.js',
            'widget/**.js'
        ]
    }
});

// 上传测试机配置
fis.config.set('deploy', {
    remote: [{
        // 远程接收地址
        receiver: 'http://123.206.205.95/to/receiver.php',
        from: '/',
        subOnly: false,
        // 注意更改服务器文件夹权限
        to: '/home/ubuntu/.fis-plus-tmp/www/template/home',
        //某些后缀的文件不进行上传
        exclude : /.*\.(?:svn|cvs|tar|rar|psd).*/
    }]
});