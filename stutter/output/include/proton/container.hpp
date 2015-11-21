namespace proton {

class container {
  public:
    container() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}