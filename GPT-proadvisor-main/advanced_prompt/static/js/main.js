if ( window.location.pathname === '/advisors' || window.location.pathname == '/get-info' ) 
{}
else if( window.location.pathname == '/signin')
{
  $("#search-form").remove();
}
else
{
    $("#search-form").remove();
}



$(function() {
    $('.category-title').each(function() {
      console.log($(this).data('color'))
      $(this).css('background-color', $(this).data('color'));
    });
  });




  var swiper = new Swiper(".mySwiper", {
    slidesPerView: 5,
    // centeredSlides: true,
    spaceBetween: 30,
    pagination: {
      el: ".swiper-pagination",
      type: "fraction",
    },
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
  });

  var appendNumber = 4;
  var prependNumber = 1;



//   home page script start

// home page script end
