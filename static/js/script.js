let index = 0;

const cards = document.querySelectorAll(".card");

function updateCarousel(){

cards.forEach((card,i)=>{

card.classList.remove("active","left","right");

if(i===index){

card.classList.add("active");

}
else if(i === (index - 1 + cards.length) % cards.length){

card.classList.add("left");

}
else if(i === (index + 1) % cards.length){

card.classList.add("right");

}

});

}

setInterval(()=>{

index = (index + 1) % cards.length;

updateCarousel();

},3000);

updateCarousel();