def search(mylist, num):
    if num==1:
        return mylist
    li = search(mylist, num-1)
    result = []

    for sub in li:
        if not isinstance(sub, list):
            sub = [sub,]

        maxindex = 0
        for obj in sub:
           index = mylist.index(obj) 
           if maxindex<index:
               maxindex = index

        for mem in mylist[maxindex+1:]:
            if mem not in sub:
                sub_temp = sub[:]
                sub.append(mem)
                result.append(sub)
                sub = sub_temp
    return result

if __name__ == '__main__':
    mylist=['x',2,r'c',4,5,'b',7]
    print(search(mylist, 2))
    print(search(mylist, 3))
