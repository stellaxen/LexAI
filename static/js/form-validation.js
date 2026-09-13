document.querySelectorAll('input[required], textarea[required]').forEach(element => {
  // Όταν προσπαθεί να υποβάλει με κενό πεδίο
  element.addEventListener('invalid', () => {
    element.setCustomValidity('Το πεδίο αυτό είναι υποχρεωτικό.');
  });

  // Όταν ο χρήστης πληκτρολογεί, καθαρίζει το λάθος
  element.addEventListener('input', () => {
    element.setCustomValidity('');
  });
});