var socket = new WebSocket('ws://' + window.location.host + '/notifications');

socket.onopen = function open() {
  console.log('WebSockets connection created.');
};

socket.onmessage = function (event) {
  if(document.getElementById("notifications")){
    document.getElementById("notifications").innerHTML += "<br>"+event.data
  }
}

if(document.getElementById("notify_form")){
document.getElementById("notify_form").addEventListener("submit",function (event){
  event.preventDefault()

  if(document.getElementById("message").value == ""){
    alert("Message should no be empty");
  }else{
  socket.send(document.getElementById("message").value);
  alert("Message broadcasted :\n"+document.getElementById("message").value+" ");
  document.getElementById("message").value = "";
  }
});
}