function removeDisruption(item) {
  const url = "/disruption-bus-stop/" + item;
  fetch(url, { method: "DELETE" })
    .then((response) => {
      if (response.ok) {
        const button = document.querySelector(
          ".disrupted-item:not(.removed)[data-bus-stop='" + item + "']"
        );
        if (button) {
          button.classList.add("removed");
        }
        const message = document.querySelector("#success_message");
        message.innerHTML = "Successfully removed disrupted " + item + "!";
      }
    })
    .catch((error) => console.error(error));
}
