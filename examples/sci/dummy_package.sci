function  [a] = dummy_eval(b)
  a = 3.0*b ;
endfunction


function  [a,b,c] = dummy_func_mat(A)
  a = 3*A(1) ;
  b = 2*A(2);
  c = 1*A(3) ;
endfunction


function  [B] = dummy_func_mat2(A)
  B=[3*A(1) ,  2*A(2), A(3)];
endfunction


function  [a,b,c,d] = dummy_func_mat_float(A,x,i)
  a = 3*A(1)*double(i) ;
  b = 2*A(2)*double(i);
  c = 1*A(3)*double(i) ;
  d = 3.1*double(i)*x;
  //e = 3*i

endfunction
