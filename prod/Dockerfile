FROM nginx
# See https://www.nginx.com/blog/deploying-nginx-nginx-plus-docker/

# This dockerfile is executed from the parent folder.,

# The public folder is generated by a hugo build.
# and is expected in the PWD that the image is being built from
COPY public /usr/share/nginx/html

# We're running from a folder above this...
# Copy our nginx configuration in.
COPY prod/etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# Enables error page which points at /404.html
# Otherwise copy the files in place...
RUN sed -i 's/\#error_page/error_page/g' /etc/nginx/conf.d/default.conf
