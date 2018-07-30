Create Environment variable AUTH with decoded as below: 

1. Open command prompt and type python(assuming python is already installed). Encode the Username and password strings to base64 using following steps
  i. import base64
  ii. base64.b64encode(<username:password>.encode('utf-8'))
  
2. Go to environmental variables under system properties and add AUTH as key and above decoded string as value. 


To install the required softwares, clone the project and open in command prompt and run below command 
    pip install -r requirements.txt
   
