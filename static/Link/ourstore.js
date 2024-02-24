$(document).ready(function() {
  $("#numbers span").each(function() {
    var number = $(this).text();
    // Split the number into an array of digits.
    var digits = number.split("");

    // Add a comma every three digits from the right.
    for (var i = digits.length - 3; i > 0; i -= 3) {
      digits.splice(i, 0, ",");
    }

    // Join the digits back into a string.
    var formattedNumber = digits.join("");

    // Set the text of the span to the formatted number.
    $(this).text(formattedNumber);
  });
});