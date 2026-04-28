# nginx/Dockerfile
FROM nginx:stable-alpine

# Remove default config and copy our config
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf

# If you have a custom HTML or extra assets, copy them here (optional)
# COPY static/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]