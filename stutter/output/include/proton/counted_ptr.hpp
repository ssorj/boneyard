namespace proton {

class counted_ptr {
  public:
    counted_ptr() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}