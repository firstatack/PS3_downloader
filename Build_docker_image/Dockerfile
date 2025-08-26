# Usa Alpine como base
FROM alpine:latest

# Instala bash, git, python3, pip, curl, jq, fzf, nano
RUN apk add --no-cache bash git python3 py3-pip jq fzf curl nano

# Crea el entorno virtual
RUN python3 -m venv /ENVLIBRAY

# Activa el entorno virtual y instala los paquetes
RUN /ENVLIBRAY/bin/pip install --upgrade pip && \
    /ENVLIBRAY/bin/pip install libray internetarchive

# Copia el script al contenedor
COPY ps3_ia_login_pkg.sh /usr/bin/ps3_ia_login_pkg.sh

# Da permisos de ejecución al script
RUN chmod +x /usr/bin/ps3_ia_login_pkg.sh

#Copiamos los ficheros pkg
RUN mkdir -p /root/.iaPS3/pkg
COPY ./pkg /root/.iaPS3/pkg

# Establece el entrypoint con bash (por si quieres pasar comandos)
ENTRYPOINT ["/bin/bash"]

# Comando por defecto al ejecutar el contenedor
CMD ["-c", "source /ENVLIBRAY/bin/activate && ps3_ia_login_pkg.sh"]
