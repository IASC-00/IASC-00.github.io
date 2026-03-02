// Live local time in nav
const timeEl = document.getElementById('nav-time');
function updateTime() {
    timeEl.textContent = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', hour12: false
    });
}
updateTime();
setInterval(updateTime, 1000);

// Active nav link highlight based on scroll position
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                navLinks.forEach(link => {
                    link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
                });
            }
        });
    },
    { rootMargin: '-45% 0px -45% 0px' }
);

sections.forEach(s => observer.observe(s));

// Scroll-reveal: fade + slide sections in as they enter the viewport
const revealObserver = new IntersectionObserver(
    (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                revealObserver.unobserve(entry.target);
            }
        });
    },
    { threshold: 0.08 }
);

document.querySelectorAll('.section').forEach(el => revealObserver.observe(el));
