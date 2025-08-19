document.addEventListener('DOMContentLoaded', function() {
    // Xử lý hiệu ứng cuộn mượt cho các liên kết neo
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Trừ đi chiều cao của header
                    behavior: 'smooth'
                });
            }
        });
    });

    // Xử lý hiệu ứng header khi cuộn
    const header = document.querySelector('header');
    let lastScrollTop = 0;

    if (header) {
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }

            if (scrollTop > lastScrollTop) {
                // Cuộn xuống
                header.style.transform = 'translateY(-100%)';
            } else {
                // Cuộn lên
                header.style.transform = 'translateY(0)';
            }

            lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
        }, { passive: true });
    }

    // Hiệu ứng hiển thị các phần tử khi cuộn đến
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature, .usage-step, .download-card');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.classList.add('visible');
            }
        });
    };

    // Thêm class cho CSS animation
    const cards = document.querySelectorAll('.feature-card, .usage-step, .download-card');
    cards.forEach(card => {
        card.classList.add('animate-on-scroll');
    });

    // Chạy animation khi trang tải và khi cuộn
    window.addEventListener('load', animateOnScroll);
    window.addEventListener('scroll', animateOnScroll, { passive: true });

    // Xử lý nút tải xuống
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Kiểm tra nếu liên kết là # (chưa có link tải)
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
                alert('Phiên bản này đang được phát triển và sẽ sớm được phát hành!');
            }
        });
    });

    // Thêm hiệu ứng cho các code block
    const codeBlocks = document.querySelectorAll('.code-block');
    codeBlocks.forEach(block => {
        // Thêm nút sao chép mã
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.title = 'Sao chép mã';
        
        block.style.position = 'relative';
        block.appendChild(copyButton);
        
        copyButton.addEventListener('click', function() {
            const code = block.querySelector('code').innerText;
            navigator.clipboard.writeText(code).then(() => {
                copyButton.innerHTML = '<i class="fas fa-check"></i>';
                setTimeout(() => {
                    copyButton.innerHTML = '<i class="fas fa-copy"></i>';
                }, 2000);
            }).catch(err => {
                console.error('Không thể sao chép: ', err);
            });
        });
    });

    // Thêm CSS cho nút sao chép
    const style = document.createElement('style');
    style.textContent = `
        .copy-button {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255, 255, 255, 0.2);
            border: none;
            border-radius: 4px;
            padding: 5px 8px;
            cursor: pointer;
            color: white;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .copy-button:hover {
            background: rgba(255, 255, 255, 0.3);
        }
        
        .animate-on-scroll {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease-out, transform 0.6s ease-out;
        }
        
        .animate-on-scroll.visible {
            opacity: 1;
            transform: translateY(0);
        }
        
        header.scrolled {
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease-in-out;
        }
    `;
    document.head.appendChild(style);
});