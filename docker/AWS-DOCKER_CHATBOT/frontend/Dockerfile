FROM nginx:1.29-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
# 메인 HTML 파일을 nginx의 기본 웹 루트에 복사
COPY index.html /usr/share/nginx/html/index.html
COPY css /usr/share/nginx/html/css
COPY js  /usr/share/nginx/html/js

# 컨테이너가 80번 포트 사용
EXPOSE 80

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=5 \
  CMD wget --quiet --spider http://127.0.0.1/nginx-health || exit 1