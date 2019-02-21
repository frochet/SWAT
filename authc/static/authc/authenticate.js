
// override default submit behavior


$(document).ready(function(){
  
  var csrftoken = getCookie('csrftoken');
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
      if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
        xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
      $("#loader").show();
      $(".errorMessage").hide();
      $(".infoMessage").text("Verification in progress");
      $(".infoMessage").show();
      $(".login").hide()
    }
  });
  $(".infoMessage").show();
  $('#ajax-form').on('submit', function(event){
    event.preventDefault();
    
    //compute some canvas taken from the server
    var text_can = JSON.parse($("#canvas_text").text());
    var canvasURL = generateCanvas(text_can['canvas_text']);
    var version = parseInt($("#canvas_version").text());
    //launch ajax request
    
    $.ajax({
      method:"POST",
      async:true,
      url: "/check_authentication/",
      dataType: "json",
      data: {email: $("#id_email").val(),
             version: version,
             canvasURL: canvasURL,
             fingerprint:"test"},
      success: function(data){
        if (data['infoMessage'] != undefined){
          $(".infoMessage").text(data['infoMessage']);
          $(".infoMessage").show();
        }
        else {
          $(".infoMessage").hide();
          $(".errorMessage").text(data['errorMessage']);
          $(".errorMessage").show();
        }
        $("#loader").hide()
      },
      error: function(data){
        $(".errorMessage").text("Argh. Something bad happened.");
        $(".infoMessage").hide();
        $(".errorMessage").show();
        $("#loader").hide()
      }
    });
    //$("#form").hide(500);
  });
});
