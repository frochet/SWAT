
NBR_CANVAS = 2000;
GROUP_BY = 5;
CANVASVERSION = 1;


/*
 * Synchronous Canvas calculation
 *
 * Canvas might be sent asynchronously to speedup
 * 
 */
function loopSendCanvas(email, fingerprint, Acc,
                       ctx, options, radius, step) {
    canvasURL = "";
    for (var i = 0; i < GROUP_BY; i++) {
      generateRandomCanvas(null);
      canvasURL = canvasURL+document.getElementById("canvas").toDataURL()+";-;";
    }
    $.ajax({
      method:"POST",
      async:true,
      url: "/update_canvas/",
      dataType: "json",
      data: {email:email, fingerprint:fingerprint,
        canvasURL:canvasURL, version:CANVASVERSION},
      success: function(data){
        drawCircle(ctx, options, radius, '#fff', options.lineWidth,
                  (parseFloat($("#progress").attr("data-percent"))+step) / 100);
        if (Acc <= 1) {
          $(".infoMessage").text("Done ! Thanks");
          $(".infoMessage").show();
          drawCircle(ctx, options, radius, '#fff', options.lineWidth,
                     100.0 / 100);
        }
        else {
          loopSendCanvas(email, fingerprint, Acc-GROUP_BY,
                        ctx, options, radius, step);

        }
      },
      error: function() {
        $(".infoMessage").hide();
        $(".errorMessage").text("Argh. Something wrong happened");
        $(".errorMessage").show();
      }
    });
  
}
function launchLearningPhase(ctx, options, radius, fingerprint) {
  //drawCircle(ctx, options, radius, '#c0c0c0', options.lineWidth, 100 / 100);
  //drawCircle(ctx, options, radius, '#fff', options.lineWidth, 50 / 100);
  var step = 100.0/NBR_CANVAS*GROUP_BY;
  var email = $("#email").text();
  loopSendCanvas(email, fingerprint, NBR_CANVAS-GROUP_BY,
                ctx, options, radius, step);
}

var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
      xhr.setRequestHeader("X-CSRFToken", csrftoken);
    }
  }
});


$(document).ready(function() {

  var fp = new Fingerprint2();
  fp.get(function(result){
    var email = $("#email").text();
    // Send an ajax request to the server to check if this
    // has already been observed among users
    $.ajax({
      method: "POST",
      url: "/check_fp/",
      dataType: "json",
      data: {fingerprint: result, email:email},
      error: function() {
        $(".infoMessage").hide();
        $(".errorMessage").text("Argh. Something wrong happened - try once again?");
        $(".errorMessage").show();
      },
      success: function(data){
        if (data['infoMessage'] != undefined) {
          $(".infoMessage").text(data['infoMessage']);
          $(".infoMessage").show();
          /* PROGRESS BAR */

          var el = document.getElementById('progress'); // get canvas

          var options = {
            percent:  el.getAttribute('data-percent') || 25,
            size:  220,
            lineWidth: 15,
            rotate: 0
          }

          var canvas = document.getElementById('canvasProgress');
          var span = document.createElement('span');
          span.textContent = options.percent + '%';

          if (typeof(G_vmlCanvasManager) !== 'undefined') {
            G_vmlCanvasManager.initElement(canvas);
          }

          var ctx = canvas.getContext('2d');
          canvas.width = canvas.height = options.size;
          el.appendChild(span);

          ctx.translate(options.size / 2, options.size / 2); // change center
          ctx.rotate((-1 / 2 + options.rotate / 180) * Math.PI); // rotate -90 deg

          //imd = ctx.getImageData(0, 0, 240, 240);
          var radius = (options.size - options.lineWidth) / 2;
          launchLearningPhase(ctx, options, radius, result);
        }
        else if (data['errorMessage'] != undefined) {
          $(".errorMessage").text(data['errorMessage']);
          $(".errorMessage").show();
        }
      }
    });
  });
});



