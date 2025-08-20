document.addEventListener('keydown', function(event) {
  const key = event.key;
  if (key === 'ArrowLeft' || key === 'a' || key === 'h') {
    const leftArrow = document.querySelector('.arrow-left');
    if (leftArrow) leftArrow.click();
  } else if (key === 'ArrowRight' || key === 'd' || key === 'l') {
    const rightArrow = document.querySelector('.arrow-right');
    if (rightArrow) rightArrow.click();
  }
});
