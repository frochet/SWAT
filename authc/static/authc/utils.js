
function csrfSafeMethod(method) {
  //these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
function getCookie(name) {
   var cookieValue = null;
   if (document.cookie && document.cookie !== '') {
     var cookies = document.cookie.split(';');
     for (var i = 0; i < cookies.length; i++) {
       var cookie = jQuery.trim(cookies[i]);
       if (cookie.substring(0, name.length+1) === (name + '=')) {
         cookieValue = decodeURIComponent(cookie.substring(name.length+1));
         break;
       }
     }
   }
   return cookieValue;
}

var drawCircle = function(ctx, options, radius, color, lineWidth, percent) {
  percent = Math.min(Math.max(0, percent || 1), 1);
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2 * percent, false);
  ctx.strokeStyle = color;
  ctx.lineCap = 'round'; // butt, round or square
  ctx.lineWidth = lineWidth
  ctx.stroke();
  $("#progress").attr("data-percent", percent*100);
  $("span").text(parseInt(percent*100,10) + '%');
};

function generateRandomText(length){
  var text = "";
  var possible = "abcdefghijklmnopqrstuvwxyz0123456789";

  for( var i=0; i < length; i++ )
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}

function getRandomColor() {
  return '#'+Math.floor(Math.random()*16777215).toString(16);
}

function generateCanvas(textList) {
  var canvas =  document.getElementById("canvas");
  var ctx = canvas.getContext("2d");
  var txt = generateRandomText(25);
  canvasURL = "";
  for (var i = 0; i < textList.length; i++) {
    //cleaning the canvas
    generateRandomCanvas(textList[i])
    canvasURL = canvasURL+document.getElementById("canvas").toDataURL()+";-;";
  }
  return canvasURL;
}

function generateRandomCanvas(txt) {
  var canvas =  document.getElementById("canvas");
  canvas.width = 280
  canvas.height = 35
  var ctx = canvas.getContext("2d");
  if (txt == null)
     txt = generateRandomText(25);
  //cleaning the canvas
  ctx.clearRect(0,0, canvas.width, canvas.height);
  //drawing the new canvas
  ctx.font= "18px 'Arial'";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#069";
  ctx.fillText(txt, 2, 15, 280);
  ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
  ctx.fillText(txt, 4, 19, 280);
  ctx.fillStyle = "#069";
  ctx.fillText(txt, 2, 23, 280);
  ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
  ctx.fillText(txt, 4, 27, 280);
  ctx.fillStyle = "#069";
  ctx.fillText(txt, 2, 31, 280);
  ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
  ctx.fillText(txt, 4, 35, 280);

}
