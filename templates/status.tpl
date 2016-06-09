<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link rel='stylesheet' type='text/css' href='/static/ansi2html.css' />
<body>

<h1>Demo {{branch}} - {{sha}} !</h1>
<p>Status: todo status</p>
<p><a href="/branches/{{branch}}/{{sha}}/dist/examples/index.html">demo</a></p>
<div class="body_foreground body_background" style="font-size: normal;">
<a onclick="active = true; follow()" href="javascript:void(0)">Follow</a>
<pre class="ansi2html-content "id="logs"></pre>
<a href="javascript:window.scrollTo(0, 0); void(0)">top</a>
</div>
<script>

let active = false;
function follow() {
    window.scrollTo(0, document.body.scrollHeight);
}
let oReq = new XMLHttpRequest();
let	logs = document.getElementById('logs');
oReq.onreadystatechange = function() {
    if (this.readyState >= 3 && this.status == 200) {
        let response = this.responseText;
        logs.insertAdjacentHTML('beforeend',response);
        //logs.innerHTML = logs.innerHTML + response;
        if (active) follow();
    }
}
oReq.open("get", "/branches/{{branch}}/{{sha}}_build.log?embed", true);
oReq.send();

document.addEventListener('wheel', a => { active = false; });
</script>

<!--
<iframe width="100%" height="100%" sandbox="allow-top-navigation allow-scripts" src="/logs/{{sha}}.log"></iframe>
-->
%end

</body> </html>
