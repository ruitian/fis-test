fis.config.merge({
	namespace : 'common',
    pack : {
        'static/pkg/aio.css' : 'widget/**.css',
        'static/pkg/aio.js' : 'widget/nav/**.js'
    }
});

// 上传测试机配置
fis.config.set('deploy', {
    remote: [{
        // 远程接收地址
        receiver: 'http://123.206.205.95/to/receiver.php',
        from: '/',
        // 是否包含‘static’文件夹
        subOnly: false,
        // 注意更改服务器文件夹权限
        to: '/home/ubuntu/.fis-plus-tmp/www/template/common',
        //某些后缀的文件不进行上传
        exclude : /.*\.(?:svn|cvs|tar|rar|psd).*/
    }]
});