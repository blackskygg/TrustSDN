#!/usr/bin/zsh

#genearate private key
openssl genrsa -out user.key 2048


# fill the information
expect <<-EOF
spawn openssl req -new -key user.key -out user.csr
expect "Country Name" 
send "CN\r"  
expect "State or Province Name" 
send "HB\r" 
expect "Locality Name" 
send "WH\r" 
expect "Organization Name" 
send "HUST\r" 
expect "Organizational Unit Name" 
send "CS\r" 
expect "Common Name" 
send "test\r" 
expect "Email Address" 
send "\r" 
expect "challenge password" 
send "123456\r" 
expect "optional company name" 
send "\r" 
interact
expect eof
EOF

#sign for the Certificate Signing Request using local CA
openssl x509 -req -in user.csr -CA cacert.pem -CAkey ./private/cakey.pem \
    -CAcreateserial -out user.crt

# get serial number of the certificate
serial=$(openssl x509 -in user.crt -serial -noout | sed 's/serial=//')

mv user.key user_$serial.key
mv user.csr ./csr/user_$serial.csr
mv user.crt user_$serial.crt
