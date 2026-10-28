"""Derive requested transport metadata from the exact launch argument list."""
def transport_settings(command):
    result={}
    for option,key in [('--useReSTIRDI','restir_di'),('--useReSTIRGI','restir_gi'),('--useReSTIRPT','restir_pt')]:
        occurrences=[i for i,value in enumerate(command) if value==option]
        if len(occurrences)>1:raise ValueError('Ambiguous duplicate renderer transport option: '+option)
        if not occurrences:
            if key=='restir_pt':result[key]=0;continue
            raise ValueError('Missing renderer transport option: '+option)
        i=occurrences[0]
        if i+1>=len(command) or command[i+1] not in ['0','1']:raise ValueError('Invalid renderer transport option: '+option)
        result[key]=int(command[i+1])
    return result
